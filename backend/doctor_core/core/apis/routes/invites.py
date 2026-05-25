from fastapi import APIRouter

from core.apis.schemas.invite import InviteAcceptResponse
from core.controllers.invite_controller import invite_controller

router = APIRouter()


@router.get("/accept", response_model=InviteAcceptResponse)
async def accept_invite(token: str) -> InviteAcceptResponse:
    return await invite_controller.accept(token)
