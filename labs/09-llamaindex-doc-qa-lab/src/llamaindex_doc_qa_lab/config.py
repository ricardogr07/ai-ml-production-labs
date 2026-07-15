from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import SettingsConfigDict

from production_labs_shared.config import BaseLabSettings

_LAB_ENV = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseLabSettings):
    # reads the CWD .env (repo root) plus the lab-local .env; lab-local wins
    model_config = SettingsConfigDict(env_file=(".env", _LAB_ENV), extra="ignore")

    llm_provider: Literal["ollama", "anthropic"] = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    anthropic_model: str = "claude-opus-4-8"
    anthropic_api_key: SecretStr | None = None

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: SecretStr | None = None
    qdrant_collection: str = "wikipedia-docs"
    embedding_model_name: str = "all-MiniLM-L6-v2"


settings = Settings()
