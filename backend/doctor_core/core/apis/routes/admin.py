from fastapi import APIRouter, Depends, HTTPException, status

from core.apis.schemas.admin import (
    AdminStatsResponse,
    AdminUserHistoryConversationResponse,
    AdminUserHistoryQuery,
    AdminUserHistoryResponse,
    CreateInviteRequest,
    InviteListItem,
)
from core.apis.schemas.common import MessageResponse
from core.controllers.admin_controller import admin_controller
from core.utils.dependencies import get_admin_user

router = APIRouter()


@router.post("/invites")
async def create_invite(payload: CreateInviteRequest, user: dict = Depends(get_admin_user)) -> dict:
    invite = await admin_controller.create_invite(payload, invited_by=user["email"])
    return {"message": "Invite sent", "invite_id": str(invite["_id"])}


@router.get("/invites", response_model=list[InviteListItem])
async def list_invites(user: dict = Depends(get_admin_user)) -> list[InviteListItem]:
    return await admin_controller.list_invites()


@router.delete("/invites/{invite_id}", response_model=MessageResponse)
async def revoke_invite(invite_id: str, user: dict = Depends(get_admin_user)) -> MessageResponse:
    return await admin_controller.revoke_invite(invite_id)


@router.get("/stats", response_model=AdminStatsResponse)
async def stats(user: dict = Depends(get_admin_user)) -> AdminStatsResponse:
    return await admin_controller.stats()


@router.get("/user-history", response_model=AdminUserHistoryResponse)
async def user_history(
    query: AdminUserHistoryQuery = Depends(),
    user: dict = Depends(get_admin_user),
) -> AdminUserHistoryResponse:
    return await admin_controller.user_history(page=query.page, page_size=query.page_size)


@router.get("/user-history/{history_id}", response_model=AdminUserHistoryConversationResponse)
async def user_history_conversation(
    history_id: str,
    user: dict = Depends(get_admin_user),
) -> AdminUserHistoryConversationResponse:
    conversation = await admin_controller.user_history_conversation(history_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation history not found.")
    return conversation
