from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CampaignDocument(BaseModel):
    campaign_id: str
    agent_id: str
    agent_name: str | None = None
    campaign_name: str
    created_by_user_id: str
    created_by_user_email: str
    # pending | running | completed | cancelled
    status: str = "pending"
    total_contacts: int = 0
    completed_contacts: int = 0
    failed_contacts: int = 0
    cancel_requested: bool = False
    created_at: datetime
    updated_at: datetime


class CampaignContactDocument(BaseModel):
    contact_id: str
    campaign_id: str
    contact_name: str | None = None
    phone_number: str
    dynamic_variables: dict[str, Any] = Field(default_factory=dict)
    # pending | calling | completed | failed | no_answer
    status: str = "pending"
    conversation_id: str | None = None
    call_started_at: datetime | None = None
    call_ended_at: datetime | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
