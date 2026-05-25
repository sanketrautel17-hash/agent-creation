from datetime import datetime

from pydantic import BaseModel, EmailStr

from core.constants.enums import InviteStatus


class InviteAcceptResponse(BaseModel):
    email: EmailStr
    token: str
    status: InviteStatus
    expires_at: datetime
