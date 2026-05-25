from datetime import datetime, timedelta, timezone
from random import randint
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config.settings import get_settings

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
ALGORITHM = "HS256"


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def ensure_utc_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def hash_secret(value: str) -> str:
    return pwd_context.hash(value)


def verify_secret(value: str, hashed_value: str) -> bool:
    return pwd_context.verify(value, hashed_value)


def generate_otp() -> str:
    return f"{randint(0, 999999):06d}"


def create_access_token(subject: str, email: str, role: str) -> str:
    settings = get_settings()
    expire = now_utc() + timedelta(hours=settings.jwt_expire_hours)
    payload = {"sub": subject, "email": email, "role": role, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid access token.") from exc
