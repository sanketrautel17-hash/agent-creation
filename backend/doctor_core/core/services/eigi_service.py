from typing import Any
from urllib.parse import urlsplit, urlunsplit

from fastapi import HTTPException, status
import httpx

from core.config.settings import get_settings
from core.utils.app_logging import get_logger


logger = get_logger(__name__)


class EigiService:
    @staticmethod
    def _extract_prompt_access_token(payload: dict[str, Any] | None) -> str:
        def find_token(value: Any) -> str:
            if isinstance(value, str):
                return value.strip()

            if isinstance(value, dict):
                for key in ("prompt_access_token", "promptAccessToken", "access_token", "accessToken"):
                    token_value = value.get(key)
                    if isinstance(token_value, str) and token_value.strip():
                        return token_value.strip()

                for nested_value in value.values():
                    nested_token = find_token(nested_value)
                    if nested_token:
                        return nested_token

            if isinstance(value, list):
                for item in value:
                    nested_token = find_token(item)
                    if nested_token:
                        return nested_token

            return ""

        if not isinstance(payload, dict):
            return ""

        return find_token(payload)

    async def list_agents(
        self,
        page: int,
        page_size: int,
        search: str | None = None,
        agent_type: str | None = None,
        agent_category: str | None = None,
    ) -> dict[str, Any]:
        settings = get_settings()
        params: dict[str, Any] = {
            "page": page,
            "page_size": page_size,
        }
        if search:
            params["search"] = search
        if agent_type:
            params["agent_type"] = agent_type
        if agent_category:
            params["agent_category"] = agent_category

        logger.info("Calling eigi list_agents url=%s params=%s", self._public_url(settings, "/agents"), params)
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            response = await client.get(
                self._public_url(settings, "/agents"),
                params=params,
                headers=self._build_headers(settings),
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise self._translate_http_error(exc, "list agents") from exc
            payload = response.json()

        if "agents" in payload and "data" not in payload:
            payload["data"] = payload.pop("agents")
        payload.setdefault("data", [])
        payload.setdefault("total", len(payload["data"]))
        payload.setdefault("page", page)
        payload.setdefault("page_size", page_size)
        payload.setdefault("total_pages", 1)
        return payload

    async def get_agent(self, agent_id: str) -> dict[str, Any]:
        settings = get_settings()
        logger.info("Calling eigi get_agent agent_id=%s url=%s", agent_id, self._public_url(settings, f"/agents/{agent_id}"))
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            response = await client.get(
                self._public_url(settings, f"/agents/{agent_id}"),
                headers=self._build_headers(settings),
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise self._translate_http_error(exc, "get the agent") from exc
            payload = response.json()

        if "agent_id" in payload and "id" not in payload:
            payload["id"] = payload["agent_id"]

        prompt_access_token = self._extract_prompt_access_token(payload)
        voice_enabled = bool(prompt_access_token)

        if not voice_enabled:
            try:
                widget_payload = await self.get_widget_agent(agent_id)
            except HTTPException as exc:
                logger.warning(
                    "Unable to fetch widget agent data while enriching agent detail agent_id=%s status=%s detail=%s",
                    agent_id,
                    exc.status_code,
                    exc.detail,
                )
            else:
                widget_prompt_access_token = self._extract_prompt_access_token(widget_payload)
                if widget_payload.get("widget_config") and not payload.get("widget_config"):
                    payload["widget_config"] = widget_payload["widget_config"]
                if widget_prompt_access_token and not payload.get("prompt_access_token"):
                    payload["prompt_access_token"] = widget_prompt_access_token
                voice_enabled = bool(widget_prompt_access_token)

        payload["voice_enabled"] = voice_enabled
        if not voice_enabled:
            payload["voice_disabled_reason"] = "Voice calls are not enabled for this agent."
        return payload

    async def get_agent_dynamic_variables(self, agent_id: str) -> dict[str, Any]:
        settings = get_settings()
        logger.info(
            "Calling eigi get_agent_dynamic_variables agent_id=%s url=%s",
            agent_id,
            self._public_url(settings, f"/agents/{agent_id}/dynamic-variables"),
        )
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            response = await client.get(
                self._public_url(settings, f"/agents/{agent_id}/dynamic-variables"),
                headers=self._build_headers(settings),
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise self._translate_http_error(exc, "get agent dynamic variables") from exc
            payload = response.json()

        payload.setdefault("agent_id", agent_id)
        payload.setdefault("dynamic_variables", [])
        return payload

    async def initialize_chat(
        self,
        agent_id: str,
        conversation_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        settings = get_settings()
        payload: dict[str, Any] = {"agent_id": agent_id}
        if conversation_metadata:
            payload["conversation_metadata"] = conversation_metadata

        logger.info("Calling eigi initialize_chat agent_id=%s url=%s", agent_id, self._widget_url(settings, "/chat/sessions"))
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.post(
                self._widget_url(settings, "/chat/sessions"),
                json=payload,
                headers=self._build_headers(settings),
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise self._translate_http_error(exc, "initialize chat") from exc
            data = response.json()

        # Ensure agent_id is present so AgentChatSessionResponse validates correctly.
        data.setdefault("agent_id", agent_id)
        return data

    async def get_widget_agent(self, agent_id: str) -> dict[str, Any]:
        settings = get_settings()
        logger.info("Calling eigi get_widget_agent agent_id=%s url=%s", agent_id, self._widget_url(settings, f"/agents/{agent_id}"))
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(
                self._widget_url(settings, f"/agents/{agent_id}"),
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise self._translate_http_error(exc, "get widget agent data") from exc
            payload = response.json()

        payload.setdefault("id", agent_id)
        return payload

    async def create_daily_voice_session(
        self,
        agent_id: str,
        conversation_metadata: dict[str, Any] | None = None,
        conversation_config_type: str = "VOICE",
        prompt_access_token: str | None = None,
    ) -> dict[str, Any]:
        resolved_prompt_access_token = (prompt_access_token or "").strip()

        agent_payload = await self.get_agent(agent_id)
        if not resolved_prompt_access_token:
            resolved_prompt_access_token = self._extract_prompt_access_token(agent_payload)

        if not resolved_prompt_access_token:
            try:
                widget_agent = await self.get_widget_agent(agent_id)
                resolved_prompt_access_token = self._extract_prompt_access_token(widget_agent)
            except HTTPException as exc:
                logger.warning(
                    "Unable to fetch widget agent data for voice session agent_id=%s status=%s detail=%s",
                    agent_id,
                    exc.status_code,
                    exc.detail,
                )

        if not resolved_prompt_access_token:
            logger.error(
                "Voice session could not start because no prompt_access_token was found for agent_id=%s",
                agent_id,
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="eigi did not return a prompt access token for this agent voice session.",
            )

        # Merge agent_id into conversation_metadata so the Pipecat bot receives it
        # inside body.client_metadata. The bot reads client_metadata.get("agent_id")
        # to start the pipeline — without this it gets None and exits silently.
        enriched_metadata: dict[str, Any] = {"agent_id": agent_id, **(conversation_metadata or {})}

        payload: dict[str, Any] = {
            "agent_id": agent_id,
            "prompt_access_token": resolved_prompt_access_token,
            "conversation_config_type": conversation_config_type or "VOICE",
            "conversation_metadata": enriched_metadata,
        }

        settings = get_settings()
        logger.info("Calling eigi create_daily_voice_session agent_id=%s url=%s", agent_id, self._widget_url(settings, "/sessions/daily"))
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            response = await client.post(
                self._widget_url(settings, "/sessions/daily"),
                json=payload,
                headers=self._build_headers(settings),
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise self._translate_http_error(exc, "create a daily voice session") from exc
            session_payload = response.json()

        session_payload.setdefault("agent_id", agent_id)
        session_payload.setdefault("metadata", conversation_metadata or {})
        return session_payload

    async def initiate_outbound_call(
        self,
        agent_id: str,
        phone_number: str,
        conversation_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Trigger an outbound call via eigi's public outbound-call API."""
        settings = get_settings()
        # Payload matches eigi's ConversationCreate schema exactly:
        # agent_id + params[{mobile_number, metadata}] + telephony_provider
        payload: dict[str, Any] = {
            "agent_id": agent_id,
            "params": [
                {
                    "mobile_number": phone_number,
                    "metadata": conversation_metadata or {},
                }
            ],
            "telephony_provider": "PLIVO",
        }

        logger.info(
            "Calling eigi initiate_outbound_call agent_id=%s phone=%s url=%s",
            agent_id,
            phone_number,
            self._public_url(settings, "/calls/outbound"),
        )
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            response = await client.post(
                self._public_url(settings, "/calls/outbound"),
                json=payload,
                headers=self._build_headers(settings),
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise self._translate_http_error(exc, "initiate outbound call") from exc
            data = response.json()

        # eigi returns conversation_id (or id) for the initiated call
        conversation_id = (
            data.get("conversation_id")
            or data.get("id")
            or data.get("call_id")
            or ""
        )
        data.setdefault("conversation_id", conversation_id)
        return data

    async def get_conversation_status(self, conversation_id: str) -> dict[str, Any]:
        """Poll a conversation's current status from eigi."""
        settings = get_settings()
        logger.info(
            "Calling eigi get_conversation_status conversation_id=%s",
            conversation_id,
        )
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            response = await client.get(
                self._public_url(settings, f"/conversations/{conversation_id}"),
                headers=self._build_headers(settings),
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise self._translate_http_error(exc, "get conversation status") from exc
            return response.json()

    async def send_chat_message(
        self,
        agent_id: str,
        message: str,
        session_id: str | None = None,
        conversation_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        settings = get_settings()
        payload: dict[str, Any] = {
            "agent_id": agent_id,
            "message": message,
            "streaming": False,
        }
        if session_id:
            payload["session_id"] = session_id
        if conversation_metadata:
            payload["metadata"] = conversation_metadata

        logger.info("Calling eigi send_chat_message agent_id=%s session_id=%s url=%s", agent_id, session_id, self._widget_url(settings, "/chat/messages"))
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            response = await client.post(
                self._widget_url(settings, "/chat/messages"),
                json=payload,
                headers=self._build_headers(settings),
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise self._translate_http_error(exc, "send a chat message") from exc

            resolved_session_id = response.headers.get("X-Session-ID") or session_id or ""

            # eigi returns a JSON body — extract the text message from known field names.
            # Fall back to raw text so unknown response shapes are still surfaced.
            response_message = ""
            raw_body = response.text.strip()
            if raw_body:
                try:
                    body = response.json()
                    response_message = (
                        body.get("response")
                        or body.get("message")
                        or body.get("text")
                        or body.get("content")
                        or body.get("answer")
                        or body.get("reply")
                        or ""
                    )
                    if not isinstance(response_message, str):
                        response_message = str(response_message)
                    response_message = response_message.strip()
                except Exception:
                    # Response is plain text — use it directly.
                    response_message = raw_body

            return {
                "agent_id": agent_id,
                "session_id": resolved_session_id,
                "response_message": response_message,
            }

    async def get_conversation_transcript(
        self,
        *,
        session_id: str | None = None,
        conversation_id: str | None = None,
    ) -> list[dict[str, Any]]:
        settings = get_settings()
        transcript_sources: list[tuple[str, str]] = []

        if session_id:
            transcript_sources.append(
                (
                    "session",
                    f"{self._normalize_base_url(settings.eigi_base_url)}/conversation/{session_id}",
                )
            )
        if conversation_id:
            transcript_sources.append(
                (
                    "conversation",
                    self._public_url(settings, f"/conversations/{conversation_id}"),
                )
            )

        for source_type, url in transcript_sources:
            logger.info("Calling eigi get_conversation_transcript source=%s url=%s", source_type, url)
            try:
                async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                    response = await client.get(
                        url,
                        headers=self._build_headers(settings),
                    )
                    response.raise_for_status()
                    payload = response.json()
            except Exception as exc:
                logger.warning(
                    "Unable to fetch eigi transcript source=%s url=%s detail=%s",
                    source_type,
                    url,
                    str(exc),
                )
                continue

            transcript = payload.get("conversation_transcript")
            if isinstance(transcript, list):
                return transcript

        return []

    @staticmethod
    def _build_headers(settings) -> dict[str, str]:
        return {"X-API-Key": EigiService._require_api_key(settings)}

    @staticmethod
    def _public_url(settings, path: str) -> str:
        return f"{EigiService._normalize_base_url(settings.eigi_base_url)}/public{path}"

    @staticmethod
    def _widget_url(settings, path: str) -> str:
        return f"{EigiService._normalize_base_url(settings.eigi_base_url)}/widgets{path}"

    @staticmethod
    def _normalize_base_url(base_url: str) -> str:
        normalized = (base_url or "").strip()
        if not normalized:
            return "https://api.eigi.ai/v1"

        normalized = normalized.rstrip("/")
        parsed = urlsplit(normalized)

        scheme = (parsed.scheme or "https").lower()
        host = (parsed.netloc or parsed.path or "").lower().strip("/")
        path = parsed.path if parsed.netloc else ""

        # Accept older/root host values and normalize them to the documented API host.
        if host in {"eigi.ai", "www.eigi.ai", "api.eigi.ai"}:
            scheme = "https"
            host = "api.eigi.ai"
            trimmed_path = path.strip("/")
            path = "/v1" if not trimmed_path else f"/{trimmed_path}"

        if not path or path == "/":
            path = "/v1"

        if not path.startswith("/"):
            path = f"/{path}"

        path = path.rstrip("/")
        if not path.endswith("/v1"):
            if path in {"/public", "/widgets"}:
                path = "/v1"
            elif path.endswith("/public") or path.endswith("/widgets"):
                path = path.rsplit("/", 1)[0]

        return urlunsplit((scheme, host, path, "", ""))

    @staticmethod
    def _require_api_key(settings) -> str:
        if not settings.eigi_api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="eigi configuration is incomplete. Missing: EIGI_API_KEY.",
            )
        return settings.eigi_api_key

    @staticmethod
    def _translate_http_error(exc: httpx.HTTPStatusError, action: str) -> HTTPException:
        response = exc.response
        detail = response.text.strip()
        logger.error(
            "eigi request failed action=%s status=%s url=%s detail=%s",
            action,
            response.status_code,
            response.request.url,
            detail[:1000],
        )

        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            return HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"eigi rejected the configured credentials while trying to {action}: {detail or 'Unauthorized.'}",
            )

        if response.status_code == status.HTTP_404_NOT_FOUND:
            return HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"eigi could not {action}: the requested agent resource was not found.",
            )

        if response.status_code == status.HTTP_403_FORBIDDEN:
            return HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"eigi denied access while trying to {action}: {detail or 'Forbidden.'}",
            )

        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"eigi failed to {action}: {detail or str(exc)}",
        )


eigi_service = EigiService()
