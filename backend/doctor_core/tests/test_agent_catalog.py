import asyncio
from pathlib import Path
import sys

service_root = Path(__file__).resolve().parents[1]
if str(service_root) not in sys.path:
    sys.path.insert(0, str(service_root))

from core.apis.schemas.agent import DynamicVariableDefinition
from core.services.admin_service import AdminService
from core.services.agent_service import AgentService
from core.controllers.agent_controller import AgentController
from core.services.eigi_service import EigiService


def test_dynamic_variable_definition_normalizes_runtime_fields() -> None:
    variable = DynamicVariableDefinition(
        variable_name="Sender Name",
        required=True,
        field_type="string",
        description="  Trusted sender name.  ",
    )

    assert variable.variable_name == "Sender_Name"
    assert variable.field_type.value == "STRING"
    assert variable.description == "Trusted sender name."


def test_agent_controller_list_agents_returns_typed_response(monkeypatch) -> None:
    async def fake_list_agents(**kwargs):
        return {
            "data": [
                {
                    "id": "agent-1",
                    "agent_name": "Doctor AI",
                    "agent_description": "Clinical assistant",
                    "agent_type": "INBOUND",
                    "agent_category": "Healthcare",
                }
            ],
            "total": 1,
            "page": 1,
            "page_size": 10,
            "total_pages": 1,
        }

    import core.controllers.agent_controller as agent_controller_module

    monkeypatch.setattr(agent_controller_module.agent_service, "list_agents", fake_list_agents)

    response = asyncio.run(
        AgentController().list_agents(
            user={"_id": "user-1"},
            page=1,
            page_size=10,
            search=None,
            agent_type=None,
            agent_category=None,
        )
    )

    assert response.total == 1
    assert response.data[0].agent_name == "Doctor AI"


def test_eigi_service_list_agents_accepts_legacy_agents_key(monkeypatch) -> None:
    class FakeResponse:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {
                "agents": [
                    {
                        "id": "agent-1",
                        "agent_name": "Doctor AI",
                    }
                ],
                "total": 1,
            }

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, url, params=None, headers=None):
            return FakeResponse()

    import core.services.eigi_service as eigi_service_module

    monkeypatch.setattr(eigi_service_module.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(
        eigi_service_module,
        "get_settings",
        lambda: type("Settings", (), {"eigi_base_url": "https://api.eigi.ai/v1", "eigi_api_key": "test-key"})(),
    )

    payload = asyncio.run(EigiService().list_agents(page=1, page_size=10))

    assert "data" in payload
    assert payload["data"][0]["id"] == "agent-1"


def test_eigi_service_initialize_chat_posts_widget_payload(monkeypatch) -> None:
    captured = {}

    class FakeResponse:
        status_code = 201

        def raise_for_status(self):
            return None

        def json(self):
            return {
                "agent_id": "agent-1",
                "session_id": "session-1",
                "first_message": "Hello John",
            }

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, url, json=None):
            captured["url"] = url
            captured["json"] = json
            return FakeResponse()

    import core.services.eigi_service as eigi_service_module

    monkeypatch.setattr(eigi_service_module.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(
        eigi_service_module,
        "get_settings",
        lambda: type("Settings", (), {"eigi_base_url": "https://api.eigi.ai/v1", "eigi_api_key": "test-key"})(),
    )

    payload = asyncio.run(
        EigiService().initialize_chat(
            agent_id="agent-1",
            conversation_metadata={"customer_name": "John"},
        )
    )

    assert captured["url"] == "https://api.eigi.ai/v1/widgets/chat/sessions"
    assert captured["json"] == {
        "agent_id": "agent-1",
        "conversation_metadata": {"customer_name": "John"},
    }
    assert payload["first_message"] == "Hello John"


def test_eigi_service_send_chat_message_returns_text_and_session_header(monkeypatch) -> None:
    class FakeResponse:
        status_code = 200
        text = "I can help with that."
        headers = {"X-Session-ID": "session-2"}

        def raise_for_status(self):
            return None

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, url, json=None):
            return FakeResponse()

    import core.services.eigi_service as eigi_service_module

    monkeypatch.setattr(eigi_service_module.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(
        eigi_service_module,
        "get_settings",
        lambda: type("Settings", (), {"eigi_base_url": "https://api.eigi.ai/v1", "eigi_api_key": "test-key"})(),
    )

    payload = asyncio.run(
        EigiService().send_chat_message(
            agent_id="agent-1",
            message="Need help",
            session_id="session-1",
            conversation_metadata={"customer_name": "John"},
        )
    )

    assert payload == {
        "agent_id": "agent-1",
        "session_id": "session-2",
        "response_message": "I can help with that.",
    }


def test_eigi_service_normalizes_legacy_root_base_url() -> None:
    assert EigiService._normalize_base_url("http://eigi.ai/") == "https://api.eigi.ai/v1"
    assert EigiService._normalize_base_url("https://api.eigi.ai") == "https://api.eigi.ai/v1"


def test_eigi_service_create_daily_voice_session_uses_prompt_token(monkeypatch) -> None:
    calls = []

    class FakeResponse:
        def __init__(self, payload, status_code=200):
            self._payload = payload
            self.status_code = status_code

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, url, headers=None):
            calls.append(("get", url, headers))
            if url.endswith("/public/agents/agent-1"):
                return FakeResponse({"id": "agent-1"})
            if url.endswith("/widgets/agents/agent-1"):
                return FakeResponse({"id": "agent-1", "prompt_access_token": "pat-123"})
            raise AssertionError(f"Unexpected GET url: {url}")

        async def post(self, url, json=None):
            calls.append(("post", url, json))
            return FakeResponse(
                {
                    "agent_id": "agent-1",
                    "conversation_id": "conv-1",
                    "dailyRoom": "https://daily.example/room",
                    "dailyToken": "token-123",
                },
                status_code=201,
            )

    import core.services.eigi_service as eigi_service_module

    monkeypatch.setattr(eigi_service_module.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(
        eigi_service_module,
        "get_settings",
        lambda: type("Settings", (), {"eigi_base_url": "https://api.eigi.ai/v1", "eigi_api_key": "test-key"})(),
    )

    payload = asyncio.run(
        EigiService().create_daily_voice_session(
            agent_id="agent-1",
            conversation_metadata={"customer_name": "John"},
            conversation_config_type="VOICE",
        )
    )

    assert calls[0] == (
        "get",
        "https://api.eigi.ai/v1/public/agents/agent-1",
        {"X-API-Key": "test-key"},
    )
    assert calls[1] == ("get", "https://api.eigi.ai/v1/widgets/agents/agent-1", None)
    assert calls[2] == (
        "post",
        "https://api.eigi.ai/v1/widgets/sessions/daily",
        {
            "agent_id": "agent-1",
            "prompt_access_token": "pat-123",
            "conversation_config_type": "VOICE",
            "conversation_metadata": {"customer_name": "John"},
        },
    )
    assert payload["dailyRoom"] == "https://daily.example/room"


def test_eigi_service_create_daily_voice_session_prefers_agent_detail_token(monkeypatch) -> None:
    calls = []

    class FakeResponse:
        def __init__(self, payload, status_code=200):
            self._payload = payload
            self.status_code = status_code

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, url, headers=None):
            calls.append(("get", url))
            if url.endswith("/public/agents/agent-1"):
                return FakeResponse({"id": "agent-1", "prompt_access_token": "pat-from-agent"})
            raise AssertionError(f"Unexpected GET url: {url}")

        async def post(self, url, json=None):
            calls.append(("post", url, json))
            return FakeResponse(
                {
                    "agent_id": "agent-1",
                    "conversation_id": "conv-1",
                    "dailyRoom": "https://daily.example/room",
                    "dailyToken": "token-123",
                },
                status_code=201,
            )

    import core.services.eigi_service as eigi_service_module

    monkeypatch.setattr(eigi_service_module.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(
        eigi_service_module,
        "get_settings",
        lambda: type("Settings", (), {"eigi_base_url": "https://api.eigi.ai/v1", "eigi_api_key": "test-key"})(),
    )

    payload = asyncio.run(
        EigiService().create_daily_voice_session(
            agent_id="agent-1",
            conversation_metadata={"customer_name": "John"},
            conversation_config_type="VOICE",
        )
    )

    assert calls == [
        ("get", "https://api.eigi.ai/v1/public/agents/agent-1"),
        (
            "post",
            "https://api.eigi.ai/v1/widgets/sessions/daily",
            {
                "agent_id": "agent-1",
                "prompt_access_token": "pat-from-agent",
                "conversation_config_type": "VOICE",
                "conversation_metadata": {"customer_name": "John"},
            },
        ),
    ]
    assert payload["dailyToken"] == "token-123"


def test_eigi_service_extract_prompt_access_token_from_nested_payload() -> None:
    payload = {
        "id": "agent-1",
        "prompt": {
            "auth": {
                "accessToken": "nested-token-123",
            }
        },
    }

    assert EigiService._extract_prompt_access_token(payload) == "nested-token-123"


def test_eigi_service_create_daily_voice_session_prefers_explicit_prompt_token(monkeypatch) -> None:
    calls = []

    class FakeResponse:
        def __init__(self, payload, status_code=200):
            self._payload = payload
            self.status_code = status_code

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, url, headers=None):
            calls.append(("get", url))
            if url.endswith("/public/agents/agent-1"):
                return FakeResponse({"id": "agent-1"})
            raise AssertionError(f"Unexpected GET url: {url}")

        async def post(self, url, json=None):
            calls.append(("post", url, json))
            return FakeResponse(
                {
                    "agent_id": "agent-1",
                    "conversation_id": "conv-1",
                    "dailyRoom": "https://daily.example/room",
                    "dailyToken": "token-123",
                },
                status_code=201,
            )

    import core.services.eigi_service as eigi_service_module

    monkeypatch.setattr(eigi_service_module.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(
        eigi_service_module,
        "get_settings",
        lambda: type("Settings", (), {"eigi_base_url": "https://api.eigi.ai/v1", "eigi_api_key": "test-key"})(),
    )

    payload = asyncio.run(
        EigiService().create_daily_voice_session(
            agent_id="agent-1",
            conversation_metadata={"customer_name": "John"},
            conversation_config_type="VOICE",
            prompt_access_token="explicit-token-123",
        )
    )

    assert calls == [
        ("get", "https://api.eigi.ai/v1/public/agents/agent-1"),
        (
            "post",
            "https://api.eigi.ai/v1/widgets/sessions/daily",
            {
                "agent_id": "agent-1",
                "prompt_access_token": "explicit-token-123",
                "conversation_config_type": "VOICE",
                "conversation_metadata": {"customer_name": "John"},
            },
        ),
    ]
    assert payload["dailyRoom"] == "https://daily.example/room"


def test_eigi_service_get_agent_marks_voice_disabled_when_no_prompt_token(monkeypatch) -> None:
    class FakeResponse:
        def __init__(self, payload, status_code=200):
            self._payload = payload
            self.status_code = status_code

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, url, headers=None):
            if url.endswith("/public/agents/agent-1"):
                return FakeResponse({"id": "agent-1", "agent_name": "Test Agent"})
            if url.endswith("/widgets/agents/agent-1"):
                return FakeResponse({"id": "agent-1", "widget_config": {"theme": "light"}})
            raise AssertionError(f"Unexpected GET url: {url}")

    import core.services.eigi_service as eigi_service_module

    monkeypatch.setattr(eigi_service_module.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(
        eigi_service_module,
        "get_settings",
        lambda: type("Settings", (), {"eigi_base_url": "https://api.eigi.ai/v1", "eigi_api_key": "test-key"})(),
    )

    payload = asyncio.run(EigiService().get_agent("agent-1"))

    assert payload["voice_enabled"] is False
    assert payload["voice_disabled_reason"] == "Voice calls are not enabled for this agent."


def test_agent_service_initialize_chat_seeds_first_message_transcript(monkeypatch) -> None:
    captured = {}

    async def fake_initialize_chat(*, agent_id, conversation_metadata):
        return {
            "agent_id": agent_id,
            "session_id": "session-123",
            "first_message": "Hello from history",
        }

    async def fake_upsert_chat_session(**kwargs):
        captured.update(kwargs)

    import core.services.agent_service as agent_service_module

    monkeypatch.setattr(agent_service_module.eigi_service, "initialize_chat", fake_initialize_chat)
    monkeypatch.setattr(agent_service_module.agent_session_crud, "upsert_chat_session", fake_upsert_chat_session)

    payload = asyncio.run(
        AgentService().initialize_chat(
            agent_id="agent-1",
            conversation_metadata={"patient_name": "John"},
            user={"_id": "user-1", "name": "Dr. Smith", "email": "dr@example.com"},
        )
    )

    assert payload["session_id"] == "session-123"
    assert captured["session_id"] == "session-123"
    assert captured["initial_transcript"] == [
        {
            "role": "assistant",
            "content": "Hello from history",
            "timestamp": captured["initial_transcript"][0]["timestamp"],
        }
    ]


def test_agent_service_send_chat_message_appends_transcript(monkeypatch) -> None:
    captured = {}

    async def fake_send_chat_message(*, agent_id, message, session_id, conversation_metadata):
        return {
            "agent_id": agent_id,
            "session_id": "session-456",
            "response_message": "I can help with that.",
        }

    async def fake_upsert_chat_session(**kwargs):
        captured["upsert"] = kwargs

    async def fake_append_chat_messages(*, session_id, messages, now):
        captured["append"] = {
            "session_id": session_id,
            "messages": messages,
            "now": now,
        }

    import core.services.agent_service as agent_service_module

    monkeypatch.setattr(agent_service_module.eigi_service, "send_chat_message", fake_send_chat_message)
    monkeypatch.setattr(agent_service_module.agent_session_crud, "upsert_chat_session", fake_upsert_chat_session)
    monkeypatch.setattr(agent_service_module.agent_session_crud, "append_chat_messages", fake_append_chat_messages)

    payload = asyncio.run(
        AgentService().send_chat_message(
            agent_id="agent-1",
            message="Need help",
            session_id="session-123",
            conversation_metadata={"patient_name": "John"},
            user={"_id": "user-1", "name": "Dr. Smith", "email": "dr@example.com"},
        )
    )

    assert payload["session_id"] == "session-456"
    assert captured["upsert"]["initial_transcript"] is None
    assert captured["append"]["session_id"] == "session-456"
    assert [message["role"] for message in captured["append"]["messages"]] == ["user", "assistant"]
    assert [message["content"] for message in captured["append"]["messages"]] == [
        "Need help",
        "I can help with that.",
    ]


def test_admin_service_get_user_history_conversation_uses_saved_transcript(monkeypatch) -> None:
    async def fake_get_by_id(history_id):
        return {
            "_id": "history-1",
            "user_id": "user-1",
            "user_name": "Patient One",
            "user_email": "patient@example.com",
            "agent_id": "agent-1",
            "agent_name": "Care Agent",
            "session_type": "chat",
            "session_id": "session-123",
            "conversation_id": None,
            "conversation_path": "/agents/agent-1?sessionId=session-123",
            "metadata": {"patient_name": "John"},
            "transcript": [
                {"role": "assistant", "content": "Hello", "timestamp": "2026-05-21T10:00:00Z"},
                {"role": "user", "content": "Need help", "timestamp": "2026-05-21T10:01:00Z"},
            ],
            "created_at": "2026-05-21T10:00:00Z",
            "last_activity_at": "2026-05-21T10:01:00Z",
        }

    async def fake_get_user_by_id(user_id):
        return {"_id": user_id, "name": "Patient One", "email": "patient@example.com"}

    async def fake_get_conversation_transcript(*, session_id=None, conversation_id=None):
        return []

    import core.services.admin_service as admin_service_module

    monkeypatch.setattr(admin_service_module.agent_session_crud, "get_by_id", fake_get_by_id)
    monkeypatch.setattr(admin_service_module.user_crud, "get_by_id", fake_get_user_by_id)
    monkeypatch.setattr(admin_service_module.eigi_service, "get_conversation_transcript", fake_get_conversation_transcript)
    monkeypatch.setattr(
        admin_service_module,
        "get_settings",
        lambda: type(
            "Settings",
            (),
            {
                "agent_id_map": {},
                "eigi_appointment_agent_id": "appointment-id",
                "eigi_followup_agent_id": "followup-id",
                "eigi_prescription_agent_id": "prescription-id",
            },
        )(),
    )

    payload = asyncio.run(AdminService().get_user_history_conversation("history-1"))

    assert payload["id"] == "history-1"
    assert payload["metadata"] == {"patient_name": "John"}
    assert payload["transcript"] == [
        {"role": "assistant", "content": "Hello", "timestamp": "2026-05-21T10:00:00Z"},
        {"role": "user", "content": "Need help", "timestamp": "2026-05-21T10:01:00Z"},
    ]
