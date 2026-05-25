from datetime import timedelta

from fastapi import HTTPException, status

from core.config.settings import get_settings
from core.cruds.otp_session_crud import otp_session_crud
from core.utils.email import email_client
from core.utils.security import ensure_utc_datetime, generate_otp, hash_secret, now_utc, verify_secret


class OtpService:
    async def issue_otp(self, email: str, purpose: str, invite_token: str | None = None) -> None:
        settings = get_settings()
        code = generate_otp()
        now = now_utc()
        await otp_session_crud.invalidate_open_sessions(email, purpose)
        await otp_session_crud.create(
            email=email,
            purpose=purpose,
            code_hash=hash_secret(code),
            expires_at=now + timedelta(minutes=settings.otp_expiry_minutes),
            invite_token=invite_token,
            now=now,
        )
        body = (
            "Your Doctor AI one-time password is "
            f"{code}. It expires in {settings.otp_expiry_minutes} minutes."
        )
        await email_client.send_message(email, "Doctor AI login code", body)

    async def verify_otp(self, email: str, purpose: str, otp: str, invite_token: str | None = None) -> dict:
        session = await otp_session_crud.get_latest(email, purpose)
        if session is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OTP session not found.")
        if session["verified"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP is no longer valid.")
        session["expires_at"] = ensure_utc_datetime(session["expires_at"])
        if session["expires_at"] < now_utc():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP has expired.")
        if session["attempts"] >= 3:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many attempts.")
        if invite_token and session.get("invite_token") != invite_token:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP session does not match invite.")
        if not verify_secret(otp, session["code_hash"]):
            await otp_session_crud.increment_attempts(session["_id"])
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP.")
        await otp_session_crud.mark_verified(session["_id"])
        return session


otp_service = OtpService()
