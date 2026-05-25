"""
Campaign service — handles all outbound calling campaign logic.

Sequential execution strategy:
  - Contact 1: call → poll until completed → Contact 2 → ...
  - Uses asyncio.sleep for polling (non-blocking).
  - cancel_requested flag allows graceful mid-campaign cancellation.
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status

from core.database.mongodb import get_collection
from core.services.eigi_service import eigi_service
from core.utils.app_logging import get_logger

logger = get_logger(__name__)

# How long to wait between each poll of the conversation status (seconds)
POLL_INTERVAL_SECONDS = 10

# Maximum time to wait for a single call to finish before marking it as failed
MAX_CALL_WAIT_SECONDS = 600  # 10 minutes


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Helpers to read / write campaign documents
# ---------------------------------------------------------------------------


async def _update_campaign(campaign_id: str, update: dict[str, Any]) -> None:
    update["updated_at"] = _now()
    await get_collection("campaigns").update_one(
        {"campaign_id": campaign_id},
        {"$set": update},
    )


async def _update_contact(contact_id: str, update: dict[str, Any]) -> None:
    update["updated_at"] = _now()
    await get_collection("campaign_contacts").update_one(
        {"contact_id": contact_id},
        {"$set": update},
    )


async def _get_campaign_doc(campaign_id: str) -> dict[str, Any] | None:
    return await get_collection("campaigns").find_one({"campaign_id": campaign_id})


# ---------------------------------------------------------------------------
# Sequential runner — runs in a background asyncio task
# ---------------------------------------------------------------------------


async def _run_campaign_sequential(campaign_id: str) -> None:
    """Background task that calls each contact one after another."""
    logger.info("Campaign %s: runner started", campaign_id)
    try:
        await _update_campaign(campaign_id, {"status": "running"})

        # Fetch contacts in insertion order (pending first)
        contacts_cursor = get_collection("campaign_contacts").find(
            {"campaign_id": campaign_id, "status": "pending"},
            sort=[("created_at", 1)],
        )
        contacts = await contacts_cursor.to_list(length=None)

        for contact in contacts:
            # Check if cancel was requested between contacts
            campaign_doc = await _get_campaign_doc(campaign_id)
            if not campaign_doc or campaign_doc.get("cancel_requested"):
                logger.info("Campaign %s: cancel requested, stopping.", campaign_id)
                await _update_campaign(campaign_id, {"status": "cancelled"})
                return

            contact_id = contact["contact_id"]
            phone_number = contact["phone_number"]
            agent_id = contact.get("agent_id") or campaign_doc.get("agent_id")

            # Build dynamic variables for this contact (all CSV columns + contact name/phone)
            conversation_metadata: dict[str, Any] = {
                **contact.get("dynamic_variables", {}),
            }
            if contact.get("contact_name"):
                conversation_metadata.setdefault("name", contact["contact_name"])
            conversation_metadata["phone_number"] = phone_number

            logger.info(
                "Campaign %s: calling contact %s at %s",
                campaign_id,
                contact_id,
                phone_number,
            )

            # Mark contact as calling
            await _update_contact(
                contact_id,
                {"status": "calling", "call_started_at": _now()},
            )

            conversation_id: str | None = None

            try:
                result = await eigi_service.initiate_outbound_call(
                    agent_id=agent_id,
                    phone_number=phone_number,
                    conversation_metadata=conversation_metadata,
                )
                conversation_id = result.get("conversation_id") or ""
                if conversation_id:
                    await _update_contact(contact_id, {"conversation_id": conversation_id})
                    logger.info(
                        "Campaign %s: contact %s call initiated, conversation_id=%s",
                        campaign_id,
                        contact_id,
                        conversation_id,
                    )
            except Exception as exc:
                logger.error(
                    "Campaign %s: failed to initiate call for contact %s — %s",
                    campaign_id,
                    contact_id,
                    exc,
                )
                await _update_contact(
                    contact_id,
                    {
                        "status": "failed",
                        "call_ended_at": _now(),
                        "error_message": str(exc)[:500],
                    },
                )
                # Increment failed counter via raw $inc (not _update_campaign which uses $set)
                await get_collection("campaigns").update_one(
                    {"campaign_id": campaign_id},
                    {"$inc": {"failed_contacts": 1}, "$set": {"updated_at": _now()}},
                )
                continue

            # ----------------------------------------------------------------
            # Poll until the conversation finishes (or timeout / cancel)
            # ----------------------------------------------------------------
            elapsed = 0
            final_status = "failed"

            while elapsed < MAX_CALL_WAIT_SECONDS:
                # Respect cancel flag
                campaign_doc = await _get_campaign_doc(campaign_id)
                if campaign_doc and campaign_doc.get("cancel_requested"):
                    logger.info("Campaign %s: cancel during polling, stopping.", campaign_id)
                    await _update_contact(
                        contact_id,
                        {"status": "failed", "call_ended_at": _now(), "error_message": "Campaign cancelled"},
                    )
                    await _update_campaign(campaign_id, {"status": "cancelled"})
                    return

                await asyncio.sleep(POLL_INTERVAL_SECONDS)
                elapsed += POLL_INTERVAL_SECONDS

                if not conversation_id:
                    # No conversation id — can't poll; treat as completed optimistically
                    final_status = "completed"
                    break

                try:
                    conv = await eigi_service.get_conversation_status(conversation_id)
                    conv_status = (
                        conv.get("status")
                        or conv.get("conversation_status")
                        or ""
                    ).lower()

                    logger.info(
                        "Campaign %s: contact %s poll — conv_status=%s elapsed=%ds",
                        campaign_id,
                        contact_id,
                        conv_status,
                        elapsed,
                    )

                    if conv_status in {"completed", "ended", "finished", "done"}:
                        final_status = "completed"
                        break
                    elif conv_status in {"failed", "error", "no_answer", "busy", "cancelled"}:
                        final_status = "no_answer" if "answer" in conv_status else "failed"
                        break
                    # Still active/ringing — keep polling

                except Exception as poll_exc:
                    logger.warning(
                        "Campaign %s: poll error for contact %s — %s",
                        campaign_id,
                        contact_id,
                        poll_exc,
                    )
                    # Don't abort; retry on next iteration

            # Timeout — treat as completed (call may still be ongoing)
            if elapsed >= MAX_CALL_WAIT_SECONDS and final_status == "failed":
                final_status = "completed"
                logger.warning(
                    "Campaign %s: contact %s timed out after %ds, marking completed",
                    campaign_id,
                    contact_id,
                    MAX_CALL_WAIT_SECONDS,
                )

            await _update_contact(
                contact_id,
                {"status": final_status, "call_ended_at": _now()},
            )

            # Increment campaign counters
            inc_field = "completed_contacts" if final_status == "completed" else "failed_contacts"
            await get_collection("campaigns").update_one(
                {"campaign_id": campaign_id},
                {"$inc": {inc_field: 1}, "$set": {"updated_at": _now()}},
            )

        # All contacts processed
        await _update_campaign(campaign_id, {"status": "completed"})
        logger.info("Campaign %s: all contacts processed — campaign completed.", campaign_id)

    except Exception as exc:
        logger.exception("Campaign %s: unexpected error in runner — %s", campaign_id, exc)
        await _update_campaign(campaign_id, {"status": "failed"})


# ---------------------------------------------------------------------------
# Public service methods
# ---------------------------------------------------------------------------


class CampaignService:
    async def create_campaign(
        self,
        agent_id: str,
        agent_name: str | None,
        campaign_name: str,
        contacts: list[dict[str, Any]],
        user: dict,
    ) -> dict[str, Any]:
        """Persist a new campaign + contacts, then start the sequential runner."""
        if not contacts:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Campaign must have at least one contact.",
            )

        campaign_id = str(uuid.uuid4())
        now = _now()

        campaign_doc = {
            "campaign_id": campaign_id,
            "agent_id": agent_id,
            "agent_name": agent_name or agent_id,
            "campaign_name": campaign_name.strip(),
            "created_by_user_id": str(user.get("_id") or user.get("id", "")),
            "created_by_user_email": user.get("email", ""),
            "status": "pending",
            "total_contacts": len(contacts),
            "completed_contacts": 0,
            "failed_contacts": 0,
            "cancel_requested": False,
            "created_at": now,
            "updated_at": now,
        }
        await get_collection("campaigns").insert_one(campaign_doc)

        # Insert contacts
        contact_docs = []
        for contact in contacts:
            raw: dict[str, Any] = {k: v for k, v in contact.items()}
            # Extract phone — check both possible key names, then remove from raw
            raw_phone = str(raw.get("phone") or raw.get("phone_number") or "").strip()
            raw.pop("phone", None)
            raw.pop("phone_number", None)

            # Sanitize phone: handle Excel scientific notation (e.g. 9.17E+11 → 917000000000)
            # and strip spaces, dashes, brackets
            try:
                # If it looks like a float/scientific notation, convert via float first
                if "e" in raw_phone.lower() and "+" in raw_phone.lower():
                    raw_phone = str(int(float(raw_phone)))
            except (ValueError, OverflowError):
                pass
            # Remove spaces, dashes, brackets, dots — keep digits and leading +
            phone_digits = "".join(c for c in raw_phone if c.isdigit() or c == "+")
            # Ensure leading + for international format
            if phone_digits and not phone_digits.startswith("+"):
                phone = "+" + phone_digits
            else:
                phone = phone_digits

            # Extract name — check both possible key names, then remove from raw
            name = str(raw.get("name") or raw.get("contact_name") or "").strip()
            raw.pop("name", None)
            raw.pop("contact_name", None)

            contact_docs.append(
                {
                    "contact_id": str(uuid.uuid4()),
                    "campaign_id": campaign_id,
                    "agent_id": agent_id,
                    "contact_name": name or None,
                    "phone_number": phone,
                    "dynamic_variables": raw,  # remaining CSV columns
                    "status": "pending",
                    "conversation_id": None,
                    "call_started_at": None,
                    "call_ended_at": None,
                    "error_message": None,
                    "created_at": now,
                    "updated_at": now,
                }
            )

        if contact_docs:
            await get_collection("campaign_contacts").insert_many(contact_docs)

        # Kick off background sequential runner
        asyncio.create_task(_run_campaign_sequential(campaign_id))
        logger.info("Campaign %s created with %d contacts, runner started.", campaign_id, len(contacts))

        campaign_doc.pop("_id", None)
        return campaign_doc

    async def list_campaigns(self, user: dict) -> list[dict[str, Any]]:
        user_id = str(user.get("_id") or user.get("id", ""))
        cursor = get_collection("campaigns").find(
            {"created_by_user_id": user_id},
            sort=[("created_at", -1)],
        )
        docs = await cursor.to_list(length=100)
        for doc in docs:
            doc.pop("_id", None)
        return docs

    async def get_campaign(self, campaign_id: str, user: dict) -> dict[str, Any]:
        user_id = str(user.get("_id") or user.get("id", ""))
        campaign = await get_collection("campaigns").find_one(
            {"campaign_id": campaign_id, "created_by_user_id": user_id}
        )
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found.",
            )
        campaign.pop("_id", None)

        # Fetch contacts
        contacts_cursor = get_collection("campaign_contacts").find(
            {"campaign_id": campaign_id},
            sort=[("created_at", 1)],
        )
        contacts = await contacts_cursor.to_list(length=None)
        for c in contacts:
            c.pop("_id", None)

        campaign["contacts"] = contacts
        return campaign

    async def cancel_campaign(self, campaign_id: str, user: dict) -> dict[str, Any]:
        user_id = str(user.get("_id") or user.get("id", ""))
        campaign = await get_collection("campaigns").find_one(
            {"campaign_id": campaign_id, "created_by_user_id": user_id}
        )
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found.",
            )
        if campaign.get("status") not in {"pending", "running"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel a campaign with status '{campaign.get('status')}'.",
            )
        await _update_campaign(campaign_id, {"cancel_requested": True})
        return {"campaign_id": campaign_id, "message": "Cancel requested. The campaign will stop after the current call finishes."}


campaign_service = CampaignService()
