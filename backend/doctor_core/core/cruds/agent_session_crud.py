from datetime import datetime
from typing import Any

from bson import ObjectId

from core.database.mongodb import get_collection


class AgentSessionCrud:
    @staticmethod
    async def upsert_chat_session(
        *,
        user: dict[str, Any],
        agent_id: str,
        agent_name: str | None,
        session_id: str,
        conversation_path: str,
        metadata: dict[str, Any],
        initial_transcript: list[dict[str, Any]] | None,
        now: datetime,
    ) -> None:
        await get_collection("agent_sessions").update_one(
            {"session_type": "chat", "session_id": session_id},
            {
                "$set": {
                    "user_id": str(user["_id"]),
                    "user_name": user.get("name") or user.get("email") or "Unknown user",
                    "user_email": user.get("email") or "",
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "session_type": "chat",
                    "session_id": session_id,
                    "conversation_id": None,
                    "conversation_path": conversation_path,
                    "metadata": metadata,
                    "updated_at": now,
                    "last_activity_at": now,
                },
                "$setOnInsert": {
                    "created_at": now,
                    "transcript": initial_transcript or [],
                },
            },
            upsert=True,
        )

    @staticmethod
    async def upsert_voice_session(
        *,
        user: dict[str, Any],
        agent_id: str,
        agent_name: str | None,
        session_id: str | None,
        conversation_id: str | None,
        conversation_path: str,
        metadata: dict[str, Any],
        now: datetime,
    ) -> None:
        lookup: dict[str, Any]
        if session_id:
            lookup = {"session_type": "voice", "session_id": session_id}
        elif conversation_id:
            lookup = {"session_type": "voice", "conversation_id": conversation_id}
        else:
            lookup = {
                "session_type": "voice",
                "user_id": str(user["_id"]),
                "agent_id": agent_id,
                "conversation_path": conversation_path,
            }

        await get_collection("agent_sessions").update_one(
            lookup,
            {
                "$set": {
                    "user_id": str(user["_id"]),
                    "user_name": user.get("name") or user.get("email") or "Unknown user",
                    "user_email": user.get("email") or "",
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "session_type": "voice",
                    "session_id": session_id,
                    "conversation_id": conversation_id,
                    "conversation_path": conversation_path,
                    "metadata": metadata,
                    "updated_at": now,
                    "last_activity_at": now,
                },
                "$setOnInsert": {
                    "created_at": now,
                    "transcript": [],
                },
            },
            upsert=True,
        )

    @staticmethod
    async def get_by_id(session_record_id: str) -> dict[str, Any] | None:
        try:
            object_id = ObjectId(session_record_id)
        except Exception:
            return None
        return await get_collection("agent_sessions").find_one({"_id": object_id})

    @staticmethod
    async def append_chat_messages(session_id: str, messages: list[dict[str, Any]], now: datetime) -> None:
        if not session_id or not messages:
            return

        await get_collection("agent_sessions").update_one(
            {"session_type": "chat", "session_id": session_id},
            {
                "$push": {
                    "transcript": {
                        "$each": messages,
                    }
                },
                "$set": {
                    "updated_at": now,
                    "last_activity_at": now,
                },
            },
        )

    @staticmethod
    async def list_recent(page: int = 1, page_size: int = 10) -> dict[str, Any]:
        skip = max(page - 1, 0) * page_size
        total = await get_collection("agent_sessions").count_documents({})
        cursor = (
            get_collection("agent_sessions")
            .find({})
            .sort("last_activity_at", -1)
            .skip(skip)
            .limit(page_size)
        )
        items = await cursor.to_list(length=page_size)
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": max((total + page_size - 1) // page_size, 1),
        }


agent_session_crud = AgentSessionCrud()
