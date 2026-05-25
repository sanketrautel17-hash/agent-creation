from core.apis.schemas.auth import AdminLoginRequest, AuthResponse, SendOtpRequest, UserResponse
from core.apis.schemas.common import MessageResponse
from core.services.auth_service import auth_service


class AuthController:
    async def send_otp(self, request, payload: SendOtpRequest) -> MessageResponse:
        await auth_service.send_otp(
            request=request,
            email=payload.email.lower(),
            purpose=payload.purpose,
            invite_token=payload.invite_token,
        )
        return MessageResponse(message="OTP sent")

    async def verify_otp(self, payload) -> AuthResponse:
        result = await auth_service.verify_otp(
            email=payload.email.lower(),
            otp=payload.otp,
            purpose=payload.purpose,
            invite_token=payload.invite_token,
            name=payload.name,
        )
        user = result["user"]
        return AuthResponse(
            access_token=result["access_token"],
            user=UserResponse(
                id=str(user["_id"]),
                email=user["email"],
                name=user["name"],
                role=user["role"],
                is_active=user["is_active"],
            ),
        )

    async def admin_login(self, payload: AdminLoginRequest) -> AuthResponse:
        result = await auth_service.admin_login(
            email=payload.email.lower(),
            password=payload.password,
        )
        user = result["user"]
        return AuthResponse(
            access_token=result["access_token"],
            user=UserResponse(
                id=str(user["_id"]),
                email=user["email"],
                name=user["name"],
                role=user["role"],
                is_active=user["is_active"],
            ),
        )


auth_controller = AuthController()
