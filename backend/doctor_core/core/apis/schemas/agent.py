from datetime import datetime
from enum import Enum
import re
from typing import Any

from fastapi import Query
from pydantic import BaseModel, ConfigDict, Field, field_validator


DYNAMIC_VARIABLE_NAME_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def canonicalize_dynamic_variable_name(value: Any) -> str:
    if value is None:
        return ""

    normalized_value = str(value).strip()
    if not normalized_value:
        return ""

    normalized_value = re.sub(r"[^a-zA-Z0-9_]+", "_", normalized_value)
    normalized_value = re.sub(r"_+", "_", normalized_value)
    if normalized_value and normalized_value[0].isdigit():
        normalized_value = f"_{normalized_value}"
    return normalized_value


class DynamicVariableFieldType(str, Enum):
    STRING = "STRING"
    NUMBER = "NUMBER"
    EMAIL = "EMAIL"
    PHONE = "PHONE"


class DynamicVariableDefinition(BaseModel):
    variable_name: str
    required: bool = False
    field_type: DynamicVariableFieldType = DynamicVariableFieldType.STRING
    description: str = ""

    @field_validator("field_type", mode="before")
    @classmethod
    def normalize_field_type(cls, value: Any) -> DynamicVariableFieldType:
        if isinstance(value, DynamicVariableFieldType):
            return value
        if hasattr(value, "value"):
            value = value.value
        if value is None:
            return DynamicVariableFieldType.STRING
        normalized_value = str(value).strip().upper()
        if not normalized_value or normalized_value == "ENUM":
            return DynamicVariableFieldType.STRING
        return DynamicVariableFieldType(normalized_value)

    @field_validator("variable_name")
    @classmethod
    def validate_variable_name(cls, value: str) -> str:
        normalized_value = canonicalize_dynamic_variable_name(value)
        if not normalized_value or not DYNAMIC_VARIABLE_NAME_PATTERN.match(normalized_value):
            raise ValueError(
                "Dynamic variable name must start with a letter or underscore and contain only letters, numbers, and underscores."
            )
        return normalized_value

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str) -> str:
        return value.strip()


class AgentListQuery:
    def __init__(
        self,
        page: int = Query(default=1, ge=1, description="Page number."),
        page_size: int = Query(default=10, ge=1, le=100, description="Items per page."),
        search: str | None = Query(default=None, description="Search in agent name and description."),
        agent_type: str | None = Query(default=None, description="Filter by agent type, for example INBOUND."),
        agent_category: str | None = Query(default=None, description="Filter by agent category."),
    ) -> None:
        self.page = page
        self.page_size = page_size
        self.search = search
        self.agent_type = agent_type
        self.agent_category = agent_category


class AgentListItem(BaseModel):
    id: str
    agent_name: str
    agent_description: str | None = None
    agent_type: str | None = None
    agent_category: str | None = None
    agent_tips: list[str] | None = None
    dynamic_variables: list[DynamicVariableDefinition] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(extra="allow")


class AgentListResponse(BaseModel):
    data: list[AgentListItem] = Field(default_factory=list)
    total: int
    page: int
    page_size: int
    total_pages: int


class AgentDetailResponse(BaseModel):
    id: str
    agent_name: str
    agent_description: str | None = None
    agent_type: str | None = None
    agent_category: str | None = None
    agent_tips: list[str] | None = None
    first_message_prompt: str | None = None
    prompt: dict[str, Any] | None = None
    stt: dict[str, Any] | None = None
    llm: dict[str, Any] | None = None
    tts: dict[str, Any] | None = None
    sts: dict[str, Any] | None = None
    tools: dict[str, Any] | None = None
    widget_config: dict[str, Any] | None = None
    dynamic_variables: list[DynamicVariableDefinition] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(extra="allow")


class AgentDynamicVariablesResponse(BaseModel):
    agent_id: str
    agent_name: str
    dynamic_variables: list[DynamicVariableDefinition] = Field(default_factory=list)


class AgentChatInitializeRequest(BaseModel):
    conversation_metadata: dict[str, Any] = Field(default_factory=dict)


class AgentChatSessionResponse(BaseModel):
    agent_id: str
    session_id: str
    first_message: str | None = None


class AgentChatMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str | None = None
    conversation_metadata: dict[str, Any] = Field(default_factory=dict)


class AgentChatMessageResponse(BaseModel):
    agent_id: str
    session_id: str
    response_message: str


class AgentVoiceSessionRequest(BaseModel):
    conversation_metadata: dict[str, Any] = Field(default_factory=dict)
    conversation_config_type: str = "VOICE"
    prompt_access_token: str | None = None


class AgentVoiceSessionResponse(BaseModel):
    id: str | None = None
    agent_id: str
    conversation_id: str | None = None
    dailyRoom: str
    dailyToken: str
    status: str | None = None
    created_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")
