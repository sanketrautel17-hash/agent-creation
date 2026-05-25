from pymongo import ASCENDING

from core.constants.enums import InviteStatus
from core.database.mongodb import get_collection


async def ensure_indexes() -> None:
    try:
        await get_collection("users").create_index([("email", ASCENDING)], unique=True)
        await get_collection("invites").create_index([("token", ASCENDING)], unique=True)
        await get_collection("agent_sessions").create_index([("user_id", ASCENDING), ("last_activity_at", ASCENDING)])
        await get_collection("agent_sessions").create_index([("agent_id", ASCENDING), ("last_activity_at", ASCENDING)])
        await get_collection("agent_sessions").create_index([("session_id", ASCENDING)])
        await get_collection("agent_sessions").create_index([("conversation_id", ASCENDING)])
        await get_collection("invites").create_index(
            [("email", ASCENDING), ("status", ASCENDING)],
            partialFilterExpression={"status": {"$in": [InviteStatus.PENDING.value, InviteStatus.ACTIVATED.value]}},
            name="invite_email_status_idx",
        )
        await get_collection("otp_sessions").create_index("expires_at", expireAfterSeconds=0)
        await get_collection("campaigns").create_index([("created_by_user_id", ASCENDING), ("created_at", ASCENDING)])
        await get_collection("campaigns").create_index([("campaign_id", ASCENDING)], unique=True)
        await get_collection("campaigns").create_index([("status", ASCENDING)])
        await get_collection("campaign_contacts").create_index([("campaign_id", ASCENDING), ("status", ASCENDING)])
        await get_collection("campaign_contacts").create_index([("contact_id", ASCENDING)], unique=True)
    except Exception:
        # Allow local app startup even when MongoDB is not available yet.
        return
