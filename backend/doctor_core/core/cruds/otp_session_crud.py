from datetime import datetime
from typing import Any, Optional

from core.database.mongodb import get_collection


class OtpSessionCrud:
    @staticmethod
    async def invalidate_open_sessions(email: str, purpose: str) -> None:
        await get_collection("otp_sessions").update_many(
            {"email": email, "purpose": purpose, "verified": False},
            {"$set": {"verified": True}},
        )

    @staticmethod
    async def create(
        email: str,
        purpose: str,
        code_hash: str,
        expires_at: datetime,
        invite_token: Optional[str],
        now: datetime,
    ) -> dict[str, Any]:
        document = {
            "email": email,
            "purpose": purpose,
            "code_hash": code_hash,
            "expires_at": expires_at,
            "attempts": 0,
            "verified": False,
            "invite_token": invite_token,
            "created_at": now,
        }
        result = await get_collection("otp_sessions").insert_one(document)
        document["_id"] = result.inserted_id
        return document

    @staticmethod
    async def get_latest(email: str, purpose: str) -> Optional[dict[str, Any]]:
        return await get_collection("otp_sessions").find_one(
            {"email": email, "purpose": purpose},
            sort=[("created_at", -1)],
        )

    @staticmethod
    async def increment_attempts(session_id) -> None:
        await get_collection("otp_sessions").update_one({"_id": session_id}, {"$inc": {"attempts": 1}})

    @staticmethod
    async def mark_verified(session_id) -> None:
        await get_collection("otp_sessions").update_one({"_id": session_id}, {"$set": {"verified": True}})


otp_session_crud = OtpSessionCrud()
