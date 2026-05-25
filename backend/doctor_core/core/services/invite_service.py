from datetime import timedelta
from uuid import uuid4

from fastapi import HTTPException, status

from core.config.settings import get_settings
from core.constants.enums import InviteStatus
from core.cruds.invite_crud import invite_crud
from core.utils.email import email_client
from core.utils.security import ensure_utc_datetime, now_utc


class InviteService:
    async def validate_invite_token(self, token: str) -> dict:
        invite = await invite_crud.get_by_token(token)
        if invite is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found.")
        if invite["status"] == InviteStatus.REVOKED.value:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invite has been revoked.")
        invite["expires_at"] = ensure_utc_datetime(invite["expires_at"])
        if invite["expires_at"] < now_utc():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invite has expired.")
        return invite

    async def create_invite(self, email: str, invited_by: str) -> dict:
        settings = get_settings()
        now = now_utc()
        token = str(uuid4())
        invite = await invite_crud.create(
            email=email,
            token=token,
            invited_by=invited_by,
            expires_at=now + timedelta(hours=settings.invite_expiry_hours),
            now=now,
        )
        accept_url = f"{settings.frontend_url}/invite/accept?token={token}"
        body = (
            "You have been invited to access the Doctor AI patient portal.\n\n"
            f"Open this link to begin signup: {accept_url}\n\n"
            "This invite expires in 72 hours."
        )
        await email_client.send_message(email, "Your Doctor AI invite", body)
        return invite


invite_service = InviteService()
