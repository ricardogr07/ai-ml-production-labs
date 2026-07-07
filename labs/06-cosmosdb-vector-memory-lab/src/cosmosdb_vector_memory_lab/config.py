"""Settings for the CosmosDB vector memory lab."""

from __future__ import annotations

from production_labs_shared.config import BaseLabSettings


class Settings(BaseLabSettings):
    cosmos_url: str = ""
    cosmos_key: str = ""
    cosmos_database: str = "vector-memory"
    cosmos_container: str = "documents"


settings = Settings()
