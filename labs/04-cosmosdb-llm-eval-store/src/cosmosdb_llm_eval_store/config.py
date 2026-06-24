"""Settings for the CosmosDB LLM eval store."""

from __future__ import annotations

from production_labs_shared.config import BaseLabSettings


class Settings(BaseLabSettings):
    cosmos_url: str = ""
    cosmos_key: str = ""
    cosmos_database: str = "llm-eval-store"
    cosmos_container: str = "evaluations"
