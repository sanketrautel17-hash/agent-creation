from urllib.parse import urlencode

from core.cruds.agent_session_crud import agent_session_crud
from core.services.eigi_service import eigi_service
from core.utils.app_logging import get_logger
from core.utils.security import now_utc


logger = get_logger(__name__)


class AgentService:
    @staticmethod
    def _build_conversation_path(agent_id: str, **query_params: str | None) -> str:
        filtered_params = {key: value for key, value in query_params.items() if value}
        if not filtered_params:
            return f"/agents/{agent_id}"
        return f"/agents/{agent_id}?{urlencode(filtered_params)}"

    async def list_agents(
        self,
        user: dict,
        page: int,
        page_size: int,
        search: str | None,
        agent_type: str | None,
        agent_category: str | None,
    ) -> dict:
        logger.info(
            "Listing eigi agents user_id=%s page=%s page_size=%s search=%s agent_type=%s agent_category=%s",
            user["_id"],
            page,
            page_size,
            search,
            agent_type,
            agent_category,
        )
        return await eigi_service.list_agents(
            page=page,
            page_size=page_size,
            search=search,
            agent_type=agent_type,
            agent_category=agent_category,
        )

    async def get_agent(self, agent_id: str, user: dict) -> dict:
        logger.info("Fetching eigi agent agent_id=%s user_id=%s", agent_id, user["_id"])
        return await eigi_service.get_agent(agent_id=agent_id)

    async def get_agent_dynamic_variables(self, agent_id: str, user: dict) -> dict:
        logger.info("Fetching eigi agent dynamic variables agent_id=%s user_id=%s", agent_id, user["_id"])
        return await eigi_service.get_agent_dynamic_variables(agent_id=agent_id)

    async def initialize_chat(
        self,
        agent_id: str,
        conversation_metadata: dict,
        user: dict,
    ) -> dict:
        logger.info("Initializing eigi chat agent_id=%s user_id=%s", agent_id, user["_id"])
        response = await eigi_service.initialize_chat(agent_id=agent_id, conversation_metadata=conversation_metadata)
        initial_transcript = []
        if response.get("first_message"):
            initial_transcript.append(
                {
                    "role": "assistant",
                    "content": response["first_message"],
                    "timestamp": now_utc(),
                }
            )
        await agent_session_crud.upsert_chat_session(
            user=user,
            agent_id=agent_id,
            agent_name=None,
            session_id=response["session_id"],
            conversation_path=self._build_conversation_path(agent_id, sessionId=response["session_id"]),
            metadata=conversation_metadata,
            initial_transcript=initial_transcript,
            now=now_utc(),
        )
        return response

    async def send_chat_message(
        self,
        agent_id: str,
        message: str,
        session_id: str | None,
        conversation_metadata: dict,
        user: dict,
    ) -> dict:
        logger.info("Sending eigi chat message agent_id=%s session_id=%s user_id=%s", agent_id, session_id, user["_id"])
        response = await eigi_service.send_chat_message(
            agent_id=agent_id,
            message=message,
            session_id=session_id,
            conversation_metadata=conversation_metadata,
        )
        resolved_session_id = response.get("session_id") or session_id or ""
        message_timestamp = now_utc()
        if resolved_session_id:
            await agent_session_crud.upsert_chat_session(
                user=user,
                agent_id=agent_id,
                agent_name=None,
                session_id=resolved_session_id,
                conversation_path=self._build_conversation_path(agent_id, sessionId=resolved_session_id),
                metadata=conversation_metadata,
                initial_transcript=None,
                now=now_utc(),
            )
            transcript_entries = [
                {
                    "role": "user",
                    "content": message,
                    "timestamp": message_timestamp,
                }
            ]
            if response.get("response_message"):
                transcript_entries.append(
                    {
                        "role": "assistant",
                        "content": response["response_message"],
                        "timestamp": now_utc(),
                    }
                )
            await agent_session_crud.append_chat_messages(
                session_id=resolved_session_id,
                messages=transcript_entries,
                now=now_utc(),
            )
        return response

    async def create_daily_voice_session(
        self,
        agent_id: str,
        conversation_metadata: dict,
        conversation_config_type: str,
        prompt_access_token: str | None,
        user: dict,
    ) -> dict:
        logger.info("Creating eigi daily voice session agent_id=%s user_id=%s", agent_id, user["_id"])
        response = await eigi_service.create_daily_voice_session(
            agent_id=agent_id,
            conversation_metadata=conversation_metadata,
            conversation_config_type=conversation_config_type,
            prompt_access_token=prompt_access_token,
        )
        await agent_session_crud.upsert_voice_session(
            user=user,
            agent_id=agent_id,
            agent_name=None,
            session_id=response.get("id"),
            conversation_id=response.get("conversation_id"),
            conversation_path=self._build_conversation_path(
                agent_id,
                voiceSessionId=response.get("id"),
                conversationId=response.get("conversation_id"),
            ),
            metadata=conversation_metadata,
            now=now_utc(),
        )
        return response


agent_service = AgentService()
