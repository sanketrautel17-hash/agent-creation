from core.apis.schemas.invite import InviteAcceptResponse
from core.services.invite_service import invite_service


class InviteController:
    async def accept(self, token: str) -> InviteAcceptResponse:
        invite = await invite_service.validate_invite_token(token)
        return InviteAcceptResponse(
            email=invite["email"],
            token=invite["token"],
            status=invite["status"],
            expires_at=invite["expires_at"],
        )


invite_controller = InviteController()
