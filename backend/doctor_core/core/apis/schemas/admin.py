from typing import Any

from datetime import datetime

from fastapi import Query
from pydantic import BaseModel, EmailStr, Field

from core.constants.enums import InviteStatus


class CreateInviteRequest(BaseModel):
    email: EmailStr


class InviteListItem(BaseModel):
    id: str
    email: EmailStr
    status: InviteStatus
    invited_by: str
    created_at: datetime
    expires_at: datetime
    accepted_at: datetime | None = None


class AdminStatsResponse(BaseModel):
    total_invites: int
    active_patients: int


class AdminUserHistoryQuery:
    def __init__(
        self,
        page: int = Query(default=1, ge=1, description="Page number."),
        page_size: int = Query(default=5, ge=1, le=100, description="Items per page."),
    ) -> None:
        self.page = page
        self.page_size = page_size


class AdminUserHistoryItem(BaseModel):
    id: str
    user_id: str
    user_name: str
    user_email: EmailStr | None = None
    agent_id: str
    agent_name: str | None = None
    session_type: str
    session_id: str | None = None
    conversation_id: str | None = None
    conversation_path: str
    created_at: datetime
    last_activity_at: datetime


class AdminUserHistoryResponse(BaseModel):
    items: list[AdminUserHistoryItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class AdminTranscriptMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime | None = None


class AdminUserHistoryConversationResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    user_email: EmailStr | None = None
    agent_id: str
    agent_name: str | None = None
    session_type: str
    session_id: str | None = None
    conversation_id: str | None = None
    conversation_path: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    transcript: list[AdminTranscriptMessage] = Field(default_factory=list)
    created_at: datetime
    last_activity_at: datetime
