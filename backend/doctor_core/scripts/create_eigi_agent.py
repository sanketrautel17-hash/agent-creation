import argparse
import asyncio
from pathlib import Path
import sys
from typing import Any

import httpx

service_root = Path(__file__).resolve().parents[1]
if str(service_root) not in sys.path:
    sys.path.insert(0, str(service_root))

from core.config.settings import get_settings


PUBLIC_API_BASE_URL = "https://api.eigi.ai/v1/public"
DEFAULT_PROVIDER_PREFERENCES = {
    "stt": [("DEEPGRAM", "nova-2"), ("WHISPER", None)],
    "llm": [("OPENAI", "gpt-4o"), ("OPENAI", "gpt-4o-mini"), ("ANTHROPIC", None), ("GOOGLE", None), ("GROK", None)],
    "tts": [("CARTESIA", "sonic-2"), ("ELEVENLABS", None), ("GOOGLE", None), ("HUME", None), ("SARVAM", None)],
}
PROMPT_TEMPLATES = {
    "appointment": (
        "You are a calm, efficient appointment scheduling assistant for a medical clinic. "
        "Help patients book, reschedule, or cancel appointments, confirm essential details, "
        "collect preferred time windows, and keep responses short, clear, and empathetic. "
        "Never invent availability. If the caller asks clinical questions, politely redirect "
        "them to the doctor or support team."
    ),
    "followup": (
        "You are a follow-up care assistant for a medical clinic. Help patients review next "
        "steps, remind them about follow-up timelines, gather symptom updates, and escalate "
        "urgent concerns to the clinic team immediately."
    ),
    "prescription": (
        "You are a prescription guidance assistant for a medical clinic. Help patients "
        "understand refill workflows, pickup expectations, and general medication instructions. "
        "Do not provide unsafe medical advice or change prescriptions."
    ),
}
FIRST_MESSAGE_TEMPLATES = {
    "appointment": "Hello, I am your appointment assistant. How can I help with your booking today?",
    "followup": "Hello, I am your follow-up care assistant. How can I support you today?",
    "prescription": "Hello, I am your prescription assistant. How can I help you today?",
}
ENV_KEY_BY_PURPOSE = {
    "appointment": "EIGI_APPOINTMENT_AGENT_ID",
    "followup": "EIGI_FOLLOWUP_AGENT_ID",
    "prescription": "EIGI_PRESCRIPTION_AGENT_ID",
}


def choose_provider_model(provider_map: dict[str, list[str]], preferences: list[tuple[str, str | None]]) -> tuple[str, str]:
    for provider_name, preferred_model in preferences:
        models = provider_map.get(provider_name) or []
        if not models:
            continue
        if preferred_model and preferred_model in models:
            return provider_name, preferred_model
        return provider_name, models[0]
    raise RuntimeError("No compatible provider/model combination was found.")


def update_env_file(env_key: str, env_value: str) -> None:
    settings = get_settings()
    env_path = Path(settings.model_config.get("env_file"))
    lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
    updated = False
    for index, line in enumerate(lines):
        if line.startswith(f"{env_key}="):
            lines[index] = f"{env_key}={env_value}"
            updated = True
            break
    if not updated:
        lines.append(f"{env_key}={env_value}")
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


async def fetch_supported_models(client: httpx.AsyncClient) -> dict[str, Any]:
    response = await client.get(f"{PUBLIC_API_BASE_URL}/providers")
    response.raise_for_status()
    return response.json()


async def fetch_voice(client: httpx.AsyncClient, provider_name: str, language: str, model_name: str | None) -> dict[str, Any]:
    params: dict[str, Any] = {"provider": provider_name, "language": language, "page_size": 10}
    if model_name:
        params["model"] = model_name
    response = await client.get(f"{PUBLIC_API_BASE_URL}/voices", params=params)
    response.raise_for_status()
    payload = response.json()
    voices = payload.get("voices") or []
    if not voices:
        raise RuntimeError(f"No voices were returned for provider {provider_name} and language {language}.")
    return voices[0]


async def create_agent(
    purpose: str,
    agent_name: str,
    language: str,
    write_env: bool,
) -> dict[str, Any]:
    settings = get_settings()
    if not settings.eigi_api_key:
        raise RuntimeError("EIGI_API_KEY is missing from backend/.env.")

    headers = {"X-API-Key": settings.eigi_api_key}
    async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
        providers_payload = await fetch_supported_models(client)
        stt_provider, stt_model = choose_provider_model(
            providers_payload.get("stt") or {},
            DEFAULT_PROVIDER_PREFERENCES["stt"],
        )
        llm_provider, llm_model = choose_provider_model(
            providers_payload.get("llm") or {},
            DEFAULT_PROVIDER_PREFERENCES["llm"],
        )
        tts_provider, tts_model = choose_provider_model(
            providers_payload.get("tts") or {},
            DEFAULT_PROVIDER_PREFERENCES["tts"],
        )
        selected_voice = await fetch_voice(client, tts_provider, language, tts_model)

        payload = {
            "agent_name": agent_name,
            "agent_type": "INBOUND",
            "agent_category": "Scheduling" if purpose == "appointment" else "Healthcare",
            "agent_description": f"{purpose.title()} agent created from the public eigi API.",
            "stt": {
                "provider_name": stt_provider,
                "model_name": stt_model,
                "language": language,
                "params": {},
            },
            "llm": {
                "provider_name": llm_provider,
                "model_name": llm_model,
                "params": {"temperature": 0.4},
            },
            "tts": {
                "provider_name": tts_provider,
                "model_name": tts_model,
                "language": language,
                "voice_id": selected_voice["id"],
                "params": {"speed": 1},
            },
            "prompt_content": PROMPT_TEMPLATES[purpose],
            "first_message_prompt": FIRST_MESSAGE_TEMPLATES[purpose],
            "tools": {
                "end_call": True,
                "set_language": {"language_string": f"{language}-{language.upper()}"},
                "user_idle": {"idle_timeout_seconds": 10, "max_retry_count": 2},
            },
        }

        response = await client.post(f"{PUBLIC_API_BASE_URL}/agents", json=payload)
        response.raise_for_status()
        agent_payload = response.json()

    if write_env:
        update_env_file(ENV_KEY_BY_PURPOSE[purpose], agent_payload["id"])

    return {
        "agent": agent_payload,
        "selected_models": {
            "stt": {"provider": stt_provider, "model": stt_model},
            "llm": {"provider": llm_provider, "model": llm_model},
            "tts": {"provider": tts_provider, "model": tts_model, "voice": selected_voice},
        },
        "env_key": ENV_KEY_BY_PURPOSE[purpose],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create an eigi agent using the documented public API.")
    parser.add_argument(
        "--purpose",
        choices=sorted(PROMPT_TEMPLATES),
        default="appointment",
        help="Agent purpose and target env slot.",
    )
    parser.add_argument(
        "--agent-name",
        default="Doctor AI Appointment Assistant",
        help="Remote eigi agent name.",
    )
    parser.add_argument(
        "--language",
        default="en",
        help="Language code for STT and TTS.",
    )
    parser.add_argument(
        "--write-env",
        action="store_true",
        help="Persist the returned eigi agent id into backend/.env.",
    )
    return parser


async def async_main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        result = await create_agent(
            purpose=args.purpose,
            agent_name=args.agent_name,
            language=args.language,
            write_env=args.write_env,
        )
    except httpx.HTTPStatusError as exc:
        body = exc.response.text.strip()
        if body:
            print(f"Agent creation failed: {body}")
        else:
            print(f"Agent creation failed: {exc}")
        return 1
    except Exception as exc:
        print(f"Agent creation failed: {exc}")
        return 1

    agent = result["agent"]
    models = result["selected_models"]
    print(f"Created eigi agent: {agent.get('id')}")
    print(f"Name: {agent.get('agent_name')}")
    print(f"STT: {models['stt']['provider']} / {models['stt']['model']}")
    print(f"LLM: {models['llm']['provider']} / {models['llm']['model']}")
    print(f"TTS: {models['tts']['provider']} / {models['tts']['model']}")
    print(f"Voice: {models['tts']['voice'].get('name')} ({models['tts']['voice'].get('id')})")
    print(f"Set {result['env_key']}={agent.get('id')}")
    if args.write_env:
        print("backend/.env updated.")
    return 0


def main() -> None:
    raise SystemExit(asyncio.run(async_main()))


if __name__ == "__main__":
    main()
