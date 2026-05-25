from datetime import datetime
from typing import Any, Optional

from bson import ObjectId

from core.database.mongodb import get_collection


class InviteCrud:
    @staticmethod
    async def get_by_token(token: str) -> Optional[dict[str, Any]]:
        return await get_collection("invites").find_one({"token": token})

    @staticmethod
    async def get_active_by_email(email: str) -> Optional[dict[str, Any]]:
        return await get_collection("invites").find_one(
            {"email": email, "status": {"$in": ["pending", "activated"]}},
            sort=[("created_at", -1)],
        )

    @staticmethod
    async def create(email: str, token: str, invited_by: str, expires_at: datetime, now: datetime) -> dict[str, Any]:
        await get_collection("invites").update_many(
            {"email": email, "status": "pending"},
            {"$set": {"status": "revoked"}},
        )
        document = {
            "email": email,
            "token": token,
            "status": "pending",
            "invited_by": invited_by,
            "expires_at": expires_at,
            "created_at": now,
            "accepted_at": None,
        }
        result = await get_collection("invites").insert_one(document)
        document["_id"] = result.inserted_id
        return document

    @staticmethod
    async def list_all() -> list[dict[str, Any]]:
        cursor = get_collection("invites").find().sort("created_at", -1)
        return await cursor.to_list(length=500)

    @staticmethod
    async def mark_activated(invite_id: str, now: datetime) -> None:
        await get_collection("invites").update_one(
            {"_id": ObjectId(invite_id)},
            {"$set": {"status": "activated", "accepted_at": now}},
        )

    @staticmethod
    async def revoke(invite_id: str) -> Optional[dict[str, Any]]:
        invite = await get_collection("invites").find_one({"_id": ObjectId(invite_id)})
        if invite is None:
            return None
        await get_collection("invites").update_one(
            {"_id": ObjectId(invite_id)},
            {"$set": {"status": "revoked"}},
        )
        invite["status"] = "revoked"
        return invite


invite_crud = InviteCrud()
