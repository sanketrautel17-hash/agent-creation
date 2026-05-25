from fastapi import APIRouter, Depends

from core.apis.schemas.campaign import (
    CampaignCancelResponse,
    CampaignCreateRequest,
    CampaignListResponse,
    CampaignResponse,
)
from core.controllers.campaign_controller import campaign_controller
from core.utils.dependencies import get_current_user

router = APIRouter()


@router.post("", response_model=CampaignResponse)
async def create_campaign(
    request: CampaignCreateRequest,
    user: dict = Depends(get_current_user),
) -> CampaignResponse:
    return await campaign_controller.create_campaign(
        agent_id=request.agent_id,
        agent_name=request.agent_name,
        campaign_name=request.campaign_name,
        contacts=request.contacts,
        user=user,
    )


@router.get("", response_model=CampaignListResponse)
async def list_campaigns(
    user: dict = Depends(get_current_user),
) -> CampaignListResponse:
    return await campaign_controller.list_campaigns(user=user)


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    user: dict = Depends(get_current_user),
) -> CampaignResponse:
    return await campaign_controller.get_campaign(campaign_id=campaign_id, user=user)


@router.post("/{campaign_id}/cancel", response_model=CampaignCancelResponse)
async def cancel_campaign(
    campaign_id: str,
    user: dict = Depends(get_current_user),
) -> CampaignCancelResponse:
    return await campaign_controller.cancel_campaign(campaign_id=campaign_id, user=user)
