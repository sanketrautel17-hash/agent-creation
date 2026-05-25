from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class CampaignCreateRequest(BaseModel):
    agent_id: str
    agent_name: str | None = None
    campaign_name: str = Field(min_length=1, max_length=200)
    # Plain list — length validated in field_validator below
    contacts: list[dict[str, Any]]

    @field_validator("contacts")
    @classmethod
    def validate_contacts(cls, contacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not contacts:
            raise ValueError("Campaign must have at least one contact.")
        for i, c in enumerate(contacts):
            phone = str(c.get("phone") or c.get("phone_number") or "").strip()
            if not phone:
                raise ValueError(f"Contact at row {i + 1} is missing a 'phone' value.")
        return contacts


class CampaignContactResponse(BaseModel):
    contact_id: str
    campaign_id: str
    contact_name: str | None = None
    phone_number: str
    dynamic_variables: dict[str, Any] = Field(default_factory=dict)
    status: str
    conversation_id: str | None = None
    call_started_at: datetime | None = None
    call_ended_at: datetime | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"extra": "ignore"}


class CampaignResponse(BaseModel):
    campaign_id: str
    agent_id: str
    agent_name: str | None = None
    campaign_name: str
    created_by_user_id: str
    created_by_user_email: str = ""
    status: str
    total_contacts: int
    completed_contacts: int
    failed_contacts: int
    cancel_requested: bool = False
    contacts: list[CampaignContactResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"extra": "ignore"}


class CampaignListResponse(BaseModel):
    data: list[CampaignResponse]
    total: int


class CampaignCancelResponse(BaseModel):
    campaign_id: str
    message: str
