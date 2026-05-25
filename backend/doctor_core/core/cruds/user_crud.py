from datetime import datetime
from typing import Any, Optional

from bson import ObjectId

from core.database.mongodb import get_collection


class UserCrud:
    @staticmethod
    async def get_by_email(email: str) -> Optional[dict[str, Any]]:
        return await get_collection("users").find_one({"email": email})

    @staticmethod
    async def get_by_id(user_id: str) -> Optional[dict[str, Any]]:
        return await get_collection("users").find_one({"_id": ObjectId(user_id)})

    @staticmethod
    async def upsert_patient(email: str, name: str, invite_id: Optional[str], now: datetime) -> dict[str, Any]:
        update = {
            "$set": {
                "email": email,
                "name": name,
                "role": "patient",
                "is_active": True,
                "invite_id": invite_id,
                "password_hash": None,
                "updated_at": now,
            },
            "$setOnInsert": {"created_at": now},
        }
        await get_collection("users").update_one({"email": email}, update, upsert=True)
        return await UserCrud.get_by_email(email)

    @staticmethod
    async def upsert_admin(email: str, name: str, password_hash: str, now: datetime) -> dict[str, Any]:
        update = {
            "$set": {
                "email": email,
                "name": name,
                "role": "admin",
                "is_active": True,
                "password_hash": password_hash,
                "updated_at": now,
            },
            "$setOnInsert": {"created_at": now},
        }
        await get_collection("users").update_one({"email": email}, update, upsert=True)
        return await UserCrud.get_by_email(email)

    @staticmethod
    async def mark_login(user_id: str, now: datetime) -> None:
        await get_collection("users").update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"last_login": now, "updated_at": now}},
        )

    @staticmethod
    async def deactivate_by_email(email: str, now: datetime) -> None:
        await get_collection("users").update_many(
            {"email": email},
            {"$set": {"is_active": False, "updated_at": now}},
        )


user_crud = UserCrud()
