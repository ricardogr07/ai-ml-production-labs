"""Settings for the RAG retrieval strategy lab."""

from __future__ import annotations

from production_labs_shared.config import BaseLabSettings


class Settings(BaseLabSettings):
    qdrant_url: str = ""
    qdrant_collection: str = "documents"


settings = Settings()
