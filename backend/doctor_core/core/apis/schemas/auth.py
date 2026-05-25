from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from core.constants.enums import OtpPurpose, UserRole


class SendOtpRequest(BaseModel):
    email: EmailStr
    purpose: OtpPurpose = OtpPurpose.LOGIN
    invite_token: Optional[str] = None
    name: Optional[str] = Field(default=None, min_length=2, max_length=120)


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)
    purpose: OtpPurpose = OtpPurpose.LOGIN
    invite_token: Optional[str] = None
    name: Optional[str] = Field(default=None, min_length=2, max_length=120)


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    name: str
    role: UserRole
    is_active: bool


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
