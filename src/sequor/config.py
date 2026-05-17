"""Application configuration loaded from .env and environment variables."""

import os

from pydantic import field_validator
from pydantic_settings import BaseSettings


# Read critical env vars BEFORE Settings() instantiation so they take precedence
# over any .env file values. This ensures actual environment variables always win.
_DATABASE_URL = os.environ.get("DATABASE_URL", "")
_JWT_SECRET = os.environ.get("JWT_SECRET", "")
_ENCRYPTION_MASTER_KEY = os.environ.get("ENCRYPTION_MASTER_KEY", "")


class Settings(BaseSettings):
    # Application
    app_env: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    # Database — use env var if set (from above preload), otherwise empty
    database_url: str = _DATABASE_URL or "postgresql://localhost:5432/sequor"

    # LLM (Ollama — free, local AI)
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "llama3.1"
    embedding_model: str = "nomic-embed-text"

    # Embeddings fallback (OpenAI — used when Ollama is unavailable)
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"

    # Email (SendGrid)
    sendgrid_api_key: str = ""
    sendgrid_webhook_verification_key: str = ""
    email_from_domain: str = "localhost"
    email_rate_limit_per_minute: int = 60

    # Billing (Stripe)
    stripe_api_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_starter_price_id: str = ""

    # Escalation defaults
    default_escalation_sla_hours: int = 4
    default_confidence_threshold: float = 0.90

    # Email retry
    email_retry_max_attempts: int = 3
    email_retry_backoff_seconds: str = "0,300,1800"

    # Encryption (base64-encoded 32-byte master key)
    encryption_master_key: str = _ENCRYPTION_MASTER_KEY

    # Auth
    jwt_secret: str = _JWT_SECRET

    # WhatsApp Business (Meta Cloud API)
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_business_account_id: str = ""
    whatsapp_app_secret: str = ""
    whatsapp_verify_token: str = ""
    whatsapp_api_version: str = "v21.0"
    whatsapp_rate_limit_per_minute: int = 250
    whatsapp_user_rate_limit_seconds: float = 6.0

    # Reverse proxy — only trust X-Forwarded-For when behind a known proxy
    trust_x_forwarded_for: bool = False

    # SLA Scheduler
    scheduler_interval_seconds: int = 300
    scheduler_enabled: bool = True

    @field_validator("scheduler_interval_seconds")
    @classmethod
    def _validate_scheduler_interval(cls, v: int) -> int:
        if v < 10:
            raise ValueError("scheduler_interval_seconds must be >= 10")
        return v

    @field_validator("default_confidence_threshold")
    @classmethod
    def _validate_confidence_threshold(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("default_confidence_threshold must be between 0.0 and 1.0")
        return v

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
