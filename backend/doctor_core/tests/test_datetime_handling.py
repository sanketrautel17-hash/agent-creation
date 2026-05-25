import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

service_root = Path(__file__).resolve().parents[1]
if str(service_root) not in sys.path:
    sys.path.insert(0, str(service_root))

from core.cruds.invite_crud import invite_crud
from core.cruds.otp_session_crud import otp_session_crud
from core.services.invite_service import InviteService
from core.services.otp_service import OtpService
from core.utils.security import ensure_utc_datetime, hash_secret


def test_ensure_utc_datetime_converts_naive_values() -> None:
    naive = datetime(2026, 5, 19, 10, 30, 0)

    normalized = ensure_utc_datetime(naive)

    assert normalized.tzinfo == timezone.utc
    assert normalized.year == naive.year
    assert normalized.month == naive.month
    assert normalized.day == naive.day


def test_validate_invite_token_accepts_legacy_naive_expiry(monkeypatch) -> None:
    async def fake_get_by_token(token: str) -> dict:
        return {
            "_id": "invite-1",
            "email": "patient@example.com",
            "token": token,
            "status": "pending",
            "expires_at": datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1),
        }

    monkeypatch.setattr(invite_crud, "get_by_token", fake_get_by_token)

    invite = asyncio.run(InviteService().validate_invite_token("invite-token"))

    assert invite["expires_at"].tzinfo == timezone.utc


def test_verify_otp_accepts_legacy_naive_expiry(monkeypatch) -> None:
    async def fake_get_latest(email: str, purpose: str) -> dict:
        return {
            "_id": "otp-1",
            "email": email,
            "purpose": purpose,
            "code_hash": hash_secret("123456"),
            "expires_at": datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=5),
            "attempts": 0,
            "verified": False,
            "invite_token": "invite-token",
        }

    async def fake_mark_verified(session_id) -> None:
        return None

    async def fake_increment_attempts(session_id) -> None:
        raise AssertionError("attempt counter should not be incremented for a valid OTP")

    monkeypatch.setattr(otp_session_crud, "get_latest", fake_get_latest)
    monkeypatch.setattr(otp_session_crud, "mark_verified", fake_mark_verified)
    monkeypatch.setattr(otp_session_crud, "increment_attempts", fake_increment_attempts)

    session = asyncio.run(
        OtpService().verify_otp(
            email="patient@example.com",
            purpose="signup",
            otp="123456",
            invite_token="invite-token",
        )
    )

    assert session["expires_at"].tzinfo == timezone.utc
