"""Application configuration loaded from .env."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # Database
    database_url: str = "postgresql://localhost:5432/sequor"

    # LLM (Ollama — free, local AI)
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "llama3.1"
    embedding_model: str = "nomic-embed-text"

    # Email (SendGrid)
    sendgrid_api_key: str = ""
    email_from_domain: str = "localhost"
    email_rate_limit_per_minute: int = 60

    # Billing (Stripe)
    stripe_api_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_starter_price_id: str = ""

    # Escalation defaults
    default_escalation_sla_hours: int = 4
    default_confidence_threshold: float = 0.90

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
