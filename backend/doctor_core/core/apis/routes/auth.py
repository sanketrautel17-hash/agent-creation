from fastapi import APIRouter, Depends, Request

from core.apis.schemas.auth import AdminLoginRequest, AuthResponse, SendOtpRequest, UserResponse, VerifyOtpRequest
from core.apis.schemas.common import MessageResponse
from core.controllers.auth_controller import auth_controller
from core.database.mongodb import get_collection
from core.utils.dependencies import get_current_user

router = APIRouter()


@router.post("/send-otp", response_model=MessageResponse)
async def send_otp(payload: SendOtpRequest, request: Request) -> MessageResponse:
    return await auth_controller.send_otp(request, payload)


@router.post("/verify-otp", response_model=AuthResponse)
async def verify_otp(payload: VerifyOtpRequest) -> AuthResponse:
    return await auth_controller.verify_otp(payload)


@router.post("/admin-login", response_model=AuthResponse)
async def admin_login(payload: AdminLoginRequest) -> AuthResponse:
    return await auth_controller.admin_login(payload)


@router.get("/me", response_model=UserResponse)
async def me(user: dict = Depends(get_current_user)) -> UserResponse:
    current_user = await get_collection("users").find_one({"email": user["email"]})
    return UserResponse(
        id=str(current_user["_id"]),
        email=current_user["email"],
        name=current_user["name"],
        role=current_user["role"],
        is_active=current_user["is_active"],
    )
