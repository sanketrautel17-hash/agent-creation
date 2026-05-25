from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from core.constants.enums import UserRole


class UserDocument(BaseModel):
    email: EmailStr
    name: str
    role: UserRole
    is_active: bool = True
    password_hash: Optional[str] = None
    invite_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
