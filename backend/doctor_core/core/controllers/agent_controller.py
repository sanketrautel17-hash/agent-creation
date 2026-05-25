from core.apis.schemas.agent import (
    AgentChatMessageResponse,
    AgentChatSessionResponse,
    AgentDetailResponse,
    AgentDynamicVariablesResponse,
    AgentListResponse,
    AgentVoiceSessionResponse,
)
from core.services.agent_service import agent_service


class AgentController:
    async def list_agents(
        self,
        user: dict,
        page: int,
        page_size: int,
        search: str | None,
        agent_type: str | None,
        agent_category: str | None,
    ) -> AgentListResponse:
        data = await agent_service.list_agents(
            user=user,
            page=page,
            page_size=page_size,
            search=search,
            agent_type=agent_type,
            agent_category=agent_category,
        )
        return AgentListResponse(**data)

    async def get_agent(self, agent_id: str, user: dict) -> AgentDetailResponse:
        data = await agent_service.get_agent(agent_id=agent_id, user=user)
        return AgentDetailResponse(**data)

    async def get_agent_dynamic_variables(self, agent_id: str, user: dict) -> AgentDynamicVariablesResponse:
        data = await agent_service.get_agent_dynamic_variables(agent_id=agent_id, user=user)
        return AgentDynamicVariablesResponse(**data)

    async def initialize_chat(
        self,
        agent_id: str,
        conversation_metadata: dict,
        user: dict,
    ) -> AgentChatSessionResponse:
        data = await agent_service.initialize_chat(
            agent_id=agent_id,
            conversation_metadata=conversation_metadata,
            user=user,
        )
        return AgentChatSessionResponse(**data)

    async def send_chat_message(
        self,
        agent_id: str,
        message: str,
        session_id: str | None,
        conversation_metadata: dict,
        user: dict,
    ) -> AgentChatMessageResponse:
        data = await agent_service.send_chat_message(
            agent_id=agent_id,
            message=message,
            session_id=session_id,
            conversation_metadata=conversation_metadata,
            user=user,
        )
        return AgentChatMessageResponse(**data)

    async def create_daily_voice_session(
        self,
        agent_id: str,
        conversation_metadata: dict,
        conversation_config_type: str,
        prompt_access_token: str | None,
        user: dict,
    ) -> AgentVoiceSessionResponse:
        data = await agent_service.create_daily_voice_session(
            agent_id=agent_id,
            conversation_metadata=conversation_metadata,
            conversation_config_type=conversation_config_type,
            prompt_access_token=prompt_access_token,
            user=user,
        )
        return AgentVoiceSessionResponse(**data)


agent_controller = AgentController()
