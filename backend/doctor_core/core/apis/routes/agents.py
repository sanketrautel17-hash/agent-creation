from fastapi import APIRouter, Depends

from core.apis.schemas.agent import (
    AgentChatInitializeRequest,
    AgentChatMessageRequest,
    AgentChatMessageResponse,
    AgentChatSessionResponse,
    AgentDetailResponse,
    AgentDynamicVariablesResponse,
    AgentListQuery,
    AgentListResponse,
    AgentVoiceSessionRequest,
    AgentVoiceSessionResponse,
)
from core.controllers.agent_controller import agent_controller
from core.utils.dependencies import get_current_user

router = APIRouter()


@router.get("", response_model=AgentListResponse)
async def list_agents(query: AgentListQuery = Depends(), user: dict = Depends(get_current_user)) -> AgentListResponse:
    return await agent_controller.list_agents(
        user=user,
        page=query.page,
        page_size=query.page_size,
        search=query.search,
        agent_type=query.agent_type,
        agent_category=query.agent_category,
    )


@router.get("/{agent_id}", response_model=AgentDetailResponse)
async def get_agent(agent_id: str, user: dict = Depends(get_current_user)) -> AgentDetailResponse:
    return await agent_controller.get_agent(agent_id=agent_id, user=user)


@router.get("/{agent_id}/dynamic-variables", response_model=AgentDynamicVariablesResponse)
async def get_agent_dynamic_variables(
    agent_id: str,
    user: dict = Depends(get_current_user),
) -> AgentDynamicVariablesResponse:
    return await agent_controller.get_agent_dynamic_variables(agent_id=agent_id, user=user)


@router.post("/{agent_id}/chat/session", response_model=AgentChatSessionResponse)
async def initialize_agent_chat(
    agent_id: str,
    request: AgentChatInitializeRequest,
    user: dict = Depends(get_current_user),
) -> AgentChatSessionResponse:
    return await agent_controller.initialize_chat(
        agent_id=agent_id,
        conversation_metadata=request.conversation_metadata,
        user=user,
    )


@router.post("/{agent_id}/chat/messages", response_model=AgentChatMessageResponse)
async def send_agent_chat_message(
    agent_id: str,
    request: AgentChatMessageRequest,
    user: dict = Depends(get_current_user),
) -> AgentChatMessageResponse:
    return await agent_controller.send_chat_message(
        agent_id=agent_id,
        message=request.message,
        session_id=request.session_id,
        conversation_metadata=request.conversation_metadata,
        user=user,
    )


@router.post("/{agent_id}/voice/session", response_model=AgentVoiceSessionResponse)
async def create_agent_voice_session(
    agent_id: str,
    request: AgentVoiceSessionRequest,
    user: dict = Depends(get_current_user),
) -> AgentVoiceSessionResponse:
    return await agent_controller.create_daily_voice_session(
        agent_id=agent_id,
        conversation_metadata=request.conversation_metadata,
        conversation_config_type=request.conversation_config_type,
        prompt_access_token=request.prompt_access_token,
        user=user,
    )
