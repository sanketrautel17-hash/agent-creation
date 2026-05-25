from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[3] / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    project_name: str = "Doctor AI Platform"
    mongo_url: str = Field(
        default="mongodb://localhost:27017/",
        validation_alias=AliasChoices("MONGODB_URL", "MONGO_DB_URL"),
    )
    database_name: str = Field(default="doctor_ai_app", validation_alias=AliasChoices("DB_NAME"))
    jwt_secret: str = Field(default="change-me", validation_alias=AliasChoices("JWT_SECRET"))
    jwt_expire_hours: int = Field(default=24, validation_alias=AliasChoices("JWT_EXPIRE_HOURS"))
    frontend_url: str = Field(default="http://localhost:5173", validation_alias=AliasChoices("FRONTEND_URL"))
    allowed_origins: list[str] = Field(default_factory=list, validation_alias=AliasChoices("ALLOWED_ORIGINS"))

    smtp_host: str = Field(default="smtp.gmail.com", validation_alias=AliasChoices("SMTP_HOST"))
    smtp_port: int = Field(default=587, validation_alias=AliasChoices("SMTP_PORT"))
    smtp_username: str = Field(
        default="",
        validation_alias=AliasChoices("SMTP_USERNAME", "GOOGLE_GMAIL_ID"),
    )
    smtp_password: str = Field(
        default="",
        validation_alias=AliasChoices("SMTP_PASSWORD", "GOOGLE_GMAIL_PASSWORD"),
    )
    from_email: str = Field(default="", validation_alias=AliasChoices("FROM_EMAIL"))

    eigi_api_key: str = Field(default="", validation_alias=AliasChoices("EIGI_API_KEY"))
    eigi_base_url: str = Field(default="https://api.eigi.ai/v1", validation_alias=AliasChoices("EIGI_BASE_URL"))
    eigi_appointment_agent_id: str = Field(default="", validation_alias=AliasChoices("EIGI_APPOINTMENT_AGENT_ID"))
    eigi_followup_agent_id: str = Field(default="", validation_alias=AliasChoices("EIGI_FOLLOWUP_AGENT_ID"))
    eigi_prescription_agent_id: str = Field(default="", validation_alias=AliasChoices("EIGI_PRESCRIPTION_AGENT_ID"))

    otp_expiry_minutes: int = Field(default=10, validation_alias=AliasChoices("OTP_EXPIRE_MINUTES"))
    invite_expiry_hours: int = Field(default=72, validation_alias=AliasChoices("INVITE_EXPIRE_HOURS"))

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: object) -> object:
        if value in (None, "", []):
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator(
        "mongo_url",
        "database_name",
        "jwt_secret",
        "frontend_url",
        "smtp_host",
        "smtp_username",
        "smtp_password",
        "from_email",
        "eigi_api_key",
        "eigi_base_url",
        "eigi_appointment_agent_id",
        "eigi_followup_agent_id",
        "eigi_prescription_agent_id",
        mode="before",
    )
    @classmethod
    def normalize_string_settings(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        normalized = value.strip()
        if len(normalized) >= 2 and normalized[0] == normalized[-1] and normalized[0] in {"'", '"'}:
            normalized = normalized[1:-1].strip()
        return normalized

    @field_validator("from_email", mode="after")
    @classmethod
    def default_from_email(cls, value: str, info) -> str:
        if value:
            return value
        username = info.data.get("smtp_username", "")
        return username or "noreply@example.com"

    @field_validator("allowed_origins", mode="after")
    @classmethod
    def fallback_allowed_origins(cls, value: list[str], info) -> list[str]:
        if value:
            return value
        origins = []
        frontend_url = info.data.get("frontend_url")
        if frontend_url:
            origins.append(frontend_url)
        return origins

    @property
    def agent_id_map(self) -> dict[str, str]:
        return {
            "appointment": self.eigi_appointment_agent_id,
            "followup": self.eigi_followup_agent_id,
            "prescription": self.eigi_prescription_agent_id,
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
