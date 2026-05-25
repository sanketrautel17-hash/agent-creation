from fastapi import HTTPException, Request, status

from core.constants.enums import InviteStatus, OtpPurpose, UserRole
from core.cruds.invite_crud import invite_crud
from core.cruds.user_crud import user_crud
from core.services.invite_service import invite_service
from core.services.otp_service import otp_service
from core.utils.rate_limit import InMemoryRateLimiter
from core.utils.security import create_access_token, now_utc, verify_secret


class AuthService:
    def __init__(self) -> None:
        self.ip_limiter = InMemoryRateLimiter(limit=5, window_seconds=60)
        self.email_limiter = InMemoryRateLimiter(limit=5, window_seconds=60)

    async def send_otp(self, request: Request, email: str, purpose: OtpPurpose, invite_token: str | None) -> None:
        client_ip = request.client.host if request.client else "unknown"
        if not self.ip_limiter.hit(f"{purpose}:{client_ip}") or not self.email_limiter.hit(f"{purpose}:{email}"):
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded.")

        user = await user_crud.get_by_email(email)
        if user and user.get("role") == UserRole.ADMIN.value and user.get("is_active"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admins must sign in with email and password.",
            )

        if purpose == OtpPurpose.SIGNUP:
            if not invite_token:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite token is required.")
            invite = await invite_service.validate_invite_token(invite_token)
            if invite["email"] != email:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite email mismatch.")
            if invite["status"] not in [InviteStatus.PENDING.value, InviteStatus.ACTIVATED.value]:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invite is not eligible.")
            await otp_service.issue_otp(email=email, purpose=purpose.value, invite_token=invite_token)
            return

        if not user or not user.get("is_active"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not authorized.")
        await otp_service.issue_otp(email=email, purpose=purpose.value)

    async def verify_otp(
        self,
        email: str,
        otp: str,
        purpose: OtpPurpose,
        invite_token: str | None,
        name: str | None,
    ) -> dict:
        user = await user_crud.get_by_email(email)
        if purpose == OtpPurpose.LOGIN and user and user.get("role") == UserRole.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admins must sign in with email and password.",
            )

        await otp_service.verify_otp(email=email, purpose=purpose.value, otp=otp, invite_token=invite_token)
        now = now_utc()

        if purpose == OtpPurpose.SIGNUP:
            if not invite_token:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite token is required.")
            invite = await invite_service.validate_invite_token(invite_token)
            resolved_name = name or (user.get("name") if user else None) or "Patient"
            user = await user_crud.upsert_patient(
                email=email,
                name=resolved_name,
                invite_id=str(invite["_id"]),
                now=now,
            )
            await invite_crud.mark_activated(str(invite["_id"]), now)

        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        if not user.get("is_active"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive.")

        await user_crud.mark_login(str(user["_id"]), now)
        access_token = create_access_token(str(user["_id"]), user["email"], user["role"])
        return {"access_token": access_token, "user": await user_crud.get_by_id(str(user["_id"]))}

    async def admin_login(self, email: str, password: str) -> dict:
        user = await user_crud.get_by_email(email)
        if user is None or user.get("role") != UserRole.ADMIN.value or not user.get("is_active"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin credentials.")

        password_hash = user.get("password_hash")
        if not password_hash or not verify_secret(password, password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin credentials.")

        now = now_utc()
        await user_crud.mark_login(str(user["_id"]), now)
        access_token = create_access_token(str(user["_id"]), user["email"], user["role"])
        return {"access_token": access_token, "user": await user_crud.get_by_id(str(user["_id"]))}


auth_service = AuthService()
