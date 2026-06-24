from __future__ import annotations

from production_labs_shared.config import BaseLabSettings


class OllamaLabSettings(BaseLabSettings):
    ollama_base_url: str = "http://localhost:11434"
    ollama_default_model: str = "phi3.5"
    ollama_timeout_seconds: float = 60.0


settings = OllamaLabSettings()
