from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from core.constants.enums import InviteStatus


class InviteDocument(BaseModel):
    email: EmailStr
    token: str
    status: InviteStatus
    invited_by: str
    expires_at: datetime
    created_at: datetime
    accepted_at: Optional[datetime] = None
