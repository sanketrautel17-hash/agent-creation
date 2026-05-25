from fastapi import APIRouter

from core.apis.routes.admin import router as admin_router
from core.apis.routes.agents import router as agents_router
from core.apis.routes.auth import router as auth_router
from core.apis.routes.campaigns import router as campaigns_router
from core.apis.routes.invites import router as invites_router
from core.apis.schemas.common import HealthResponse

api_router = APIRouter()


@api_router.get("/health", response_model=HealthResponse, tags=["system"])
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", message="Doctor AI API is running.")


api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(invites_router, prefix="/invites", tags=["invites"])
api_router.include_router(admin_router, prefix="/admin", tags=["admin"])
api_router.include_router(agents_router, prefix="/agents", tags=["agents"])
api_router.include_router(campaigns_router, prefix="/campaigns", tags=["campaigns"])
