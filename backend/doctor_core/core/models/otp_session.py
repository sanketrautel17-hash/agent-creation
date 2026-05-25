from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from core.constants.enums import OtpPurpose


class OtpSessionDocument(BaseModel):
    email: EmailStr
    purpose: OtpPurpose
    code_hash: str
    expires_at: datetime
    attempts: int = 0
    verified: bool = False
    invite_token: Optional[str] = None
    created_at: datetime
