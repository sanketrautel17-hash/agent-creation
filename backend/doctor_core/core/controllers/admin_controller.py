from core.apis.schemas.admin import (
    AdminStatsResponse,
    AdminUserHistoryConversationResponse,
    AdminUserHistoryItem,
    AdminUserHistoryResponse,
    CreateInviteRequest,
    InviteListItem,
)
from core.apis.schemas.common import MessageResponse
from core.services.admin_service import admin_service


class AdminController:
    async def create_invite(self, payload: CreateInviteRequest, invited_by: str) -> dict:
        return await admin_service.create_invite(email=payload.email.lower(), invited_by=invited_by)

    async def list_invites(self) -> list[InviteListItem]:
        invites = await admin_service.list_invites()
        return [
            InviteListItem(
                id=str(invite["_id"]),
                email=invite["email"],
                status=invite["status"],
                invited_by=invite["invited_by"],
                created_at=invite["created_at"],
                expires_at=invite["expires_at"],
                accepted_at=invite.get("accepted_at"),
            )
            for invite in invites
        ]

    async def revoke_invite(self, invite_id: str) -> MessageResponse:
        await admin_service.revoke_invite(invite_id)
        return MessageResponse(message="Invite revoked")

    async def stats(self) -> AdminStatsResponse:
        data = await admin_service.get_stats()
        return AdminStatsResponse(**data)

    async def user_history(self, page: int, page_size: int) -> AdminUserHistoryResponse:
        history = await admin_service.get_user_history(page=page, page_size=page_size)
        return AdminUserHistoryResponse(
            items=[
                AdminUserHistoryItem(
                    id=str(item["_id"]),
                    user_id=item["user_id"],
                    user_name=item["user_name"],
                    user_email=item.get("user_email") or None,
                    agent_id=item["agent_id"],
                    agent_name=item.get("agent_name"),
                    session_type=item["session_type"],
                    session_id=item.get("session_id"),
                    conversation_id=item.get("conversation_id"),
                    conversation_path=item["conversation_path"],
                    created_at=item["created_at"],
                    last_activity_at=item["last_activity_at"],
                )
                for item in history["items"]
            ],
            total=history["total"],
            page=history["page"],
            page_size=history["page_size"],
            total_pages=history["total_pages"],
        )

    async def user_history_conversation(self, history_id: str) -> AdminUserHistoryConversationResponse | None:
        history_item = await admin_service.get_user_history_conversation(history_id)
        if history_item is None:
            return None

        return AdminUserHistoryConversationResponse(**history_item)


admin_controller = AdminController()
