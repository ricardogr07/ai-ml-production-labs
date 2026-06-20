from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseLabSettings(BaseSettings):
    """Base settings shared across all labs."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "local"
    log_level: str = "INFO"
    otel_service_name: str = "ai-ml-production-lab"
    otel_exporter_otlp_endpoint: str = ""
