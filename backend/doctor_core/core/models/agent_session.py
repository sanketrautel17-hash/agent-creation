from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AgentSessionDocument(BaseModel):
    user_id: str
    user_name: str
    user_email: str
    agent_id: str
    agent_name: str | None = None
    session_type: str
    session_id: str | None = None
    conversation_id: str | None = None
    conversation_path: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    transcript: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    last_activity_at: datetime
