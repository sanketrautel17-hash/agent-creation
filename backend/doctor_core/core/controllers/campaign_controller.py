from typing import Any

from core.apis.schemas.campaign import (
    CampaignCancelResponse,
    CampaignListResponse,
    CampaignResponse,
)
from core.services.campaign_service import campaign_service


class CampaignController:
    async def create_campaign(
        self,
        agent_id: str,
        agent_name: str | None,
        campaign_name: str,
        contacts: list[dict[str, Any]],
        user: dict,
    ) -> CampaignResponse:
        data = await campaign_service.create_campaign(
            agent_id=agent_id,
            agent_name=agent_name,
            campaign_name=campaign_name,
            contacts=contacts,
            user=user,
        )
        # Newly created campaign has no contacts list yet in response
        data.setdefault("contacts", [])
        return CampaignResponse(**data)

    async def list_campaigns(self, user: dict) -> CampaignListResponse:
        campaigns = await campaign_service.list_campaigns(user=user)
        items = []
        for c in campaigns:
            c.setdefault("contacts", [])
            items.append(CampaignResponse(**c))
        return CampaignListResponse(data=items, total=len(items))

    async def get_campaign(self, campaign_id: str, user: dict) -> CampaignResponse:
        data = await campaign_service.get_campaign(campaign_id=campaign_id, user=user)
        return CampaignResponse(**data)

    async def cancel_campaign(self, campaign_id: str, user: dict) -> CampaignCancelResponse:
        data = await campaign_service.cancel_campaign(campaign_id=campaign_id, user=user)
        return CampaignCancelResponse(**data)


campaign_controller = CampaignController()
