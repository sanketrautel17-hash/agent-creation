from urllib.parse import urlencode

from core.config.settings import get_settings
from core.cruds.agent_session_crud import agent_session_crud
from core.cruds.invite_crud import invite_crud
from core.cruds.user_crud import user_crud
from core.database.mongodb import get_collection
from core.services.eigi_service import eigi_service
from core.services.invite_service import invite_service
from core.utils.security import now_utc


class AdminService:
    @staticmethod
    def _normalize_transcript_entry(entry: dict) -> dict | None:
        if not isinstance(entry, dict):
            return None

        role = str(entry.get("role") or "").strip().lower()
        if role in {"human", "patient"}:
            role = "user"
        elif role in {"bot", "agent"}:
            role = "assistant"

        content = entry.get("content")
        if content is None:
            content = entry.get("message")
        if content is None:
            content = entry.get("text")

        content_text = str(content or "").strip()
        if not role or not content_text:
            return None

        timestamp = entry.get("timestamp") or entry.get("created_at")
        return {
            "role": role,
            "content": content_text,
            "timestamp": timestamp,
        }

    @classmethod
    def _normalize_transcript(cls, transcript: object) -> list[dict]:
        if not isinstance(transcript, list):
            return []

        normalized_transcript = []
        for entry in transcript:
            normalized_entry = cls._normalize_transcript_entry(entry)
            if normalized_entry:
                normalized_transcript.append(normalized_entry)
        return normalized_transcript

    @staticmethod
    def _fallback_agent_name(agent_type: str | None) -> str | None:
        labels = {
            "appointment": "Appointment Agent",
            "followup": "Follow-up Agent",
            "prescription": "Prescription Agent",
        }
        if not agent_type:
            return None
        return labels.get(str(agent_type).lower(), str(agent_type).replace("_", " ").title())

    @staticmethod
    def _fallback_agent_name_from_id(agent_id: str | None, settings) -> str | None:
        if not agent_id:
            return None
        reverse_map = {
            settings.eigi_appointment_agent_id: "Appointment Agent",
            settings.eigi_followup_agent_id: "Follow-up Agent",
            settings.eigi_prescription_agent_id: "Prescription Agent",
        }
        return reverse_map.get(agent_id)

    @staticmethod
    def _build_conversation_path(agent_id: str, session_type: str, session_id: str | None, conversation_id: str | None) -> str:
        params: dict[str, str] = {}
        if session_type == "voice":
            if session_id:
                params["voiceSessionId"] = session_id
            if conversation_id:
                params["conversationId"] = conversation_id
        else:
            if session_id:
                params["sessionId"] = session_id
            if conversation_id:
                params["conversationId"] = conversation_id

        if not params:
            return f"/agents/{agent_id}"

        return f"/agents/{agent_id}?{urlencode(params)}"

    async def create_invite(self, email: str, invited_by: str) -> dict:
        return await invite_service.create_invite(email=email, invited_by=invited_by)

    async def list_invites(self) -> list[dict]:
        return await invite_crud.list_all()

    async def revoke_invite(self, invite_id: str) -> None:
        invite = await invite_crud.revoke(invite_id)
        if invite is None:
            return
        await user_crud.deactivate_by_email(invite["email"], now_utc())

    async def get_stats(self) -> dict[str, int]:
        total_invites = await get_collection("invites").count_documents({})
        active_patients = await get_collection("users").count_documents({"role": "patient", "is_active": True})
        return {
            "total_invites": total_invites,
            "active_patients": active_patients,
        }

    async def get_user_history(self, page: int = 1, page_size: int = 10) -> dict:
        history_page = await agent_session_crud.list_recent(page=page, page_size=page_size)
        settings = get_settings()
        normalized_history: list[dict] = []

        for item in history_page["items"]:
            user_id = str(item.get("user_id") or "")
            user = await user_crud.get_by_id(user_id) if user_id else None

            agent_type = item.get("agent_type")
            agent_id = item.get("agent_id") or settings.agent_id_map.get(str(agent_type or "").lower(), "")
            session_type = item.get("session_type") or item.get("session_mode") or "chat"
            session_id = item.get("session_id") or item.get("eigi_session_id")
            conversation_id = item.get("conversation_id")
            created_at = item.get("created_at") or item.get("started_at") or item.get("updated_at") or now_utc()
            last_activity_at = (
                item.get("last_activity_at")
                or item.get("updated_at")
                or item.get("ended_at")
                or item.get("started_at")
                or created_at
            )

            normalized_history.append(
                {
                    "_id": item["_id"],
                    "user_id": user_id,
                    "user_name": item.get("user_name") or (user.get("name") if user else None) or "Unknown user",
                    "user_email": item.get("user_email") or (user.get("email") if user else None),
                    "agent_id": agent_id,
                    "agent_name": item.get("agent_name")
                    or self._fallback_agent_name(agent_type)
                    or self._fallback_agent_name_from_id(agent_id, settings),
                    "session_type": session_type,
                    "session_id": session_id,
                    "conversation_id": conversation_id,
                    "conversation_path": item.get("conversation_path")
                    or self._build_conversation_path(agent_id, session_type, session_id, conversation_id),
                    "created_at": created_at,
                    "last_activity_at": last_activity_at,
                }
            )

        return {
            "items": normalized_history,
            "total": history_page["total"],
            "page": history_page["page"],
            "page_size": history_page["page_size"],
            "total_pages": history_page["total_pages"],
        }

    async def get_user_history_conversation(self, history_id: str) -> dict | None:
        item = await agent_session_crud.get_by_id(history_id)
        if not item:
            return None

        user_id = str(item.get("user_id") or "")
        user = await user_crud.get_by_id(user_id) if user_id else None
        settings = get_settings()
        agent_type = item.get("agent_type")
        agent_id = item.get("agent_id") or settings.agent_id_map.get(str(agent_type or "").lower(), "")
        session_type = item.get("session_type") or item.get("session_mode") or "chat"
        session_id = item.get("session_id") or item.get("eigi_session_id")
        conversation_id = item.get("conversation_id")
        created_at = item.get("created_at") or item.get("started_at") or item.get("updated_at") or now_utc()
        last_activity_at = (
            item.get("last_activity_at")
            or item.get("updated_at")
            or item.get("ended_at")
            or item.get("started_at")
            or created_at
        )

        stored_transcript = self._normalize_transcript(item.get("transcript"))
        transcript = stored_transcript
        if not transcript:
            remote_transcript = await eigi_service.get_conversation_transcript(
                session_id=session_id if session_type == "chat" else None,
                conversation_id=conversation_id,
            )
            transcript = self._normalize_transcript(remote_transcript)

        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}

        return {
            "id": str(item["_id"]),
            "user_id": user_id,
            "user_name": item.get("user_name") or (user.get("name") if user else None) or "Unknown user",
            "user_email": item.get("user_email") or (user.get("email") if user else None),
            "agent_id": agent_id,
            "agent_name": item.get("agent_name")
            or self._fallback_agent_name(agent_type)
            or self._fallback_agent_name_from_id(agent_id, settings),
            "session_type": session_type,
            "session_id": session_id,
            "conversation_id": conversation_id,
            "conversation_path": item.get("conversation_path")
            or self._build_conversation_path(agent_id, session_type, session_id, conversation_id),
            "metadata": metadata,
            "transcript": transcript,
            "created_at": created_at,
            "last_activity_at": last_activity_at,
        }


admin_service = AdminService()
