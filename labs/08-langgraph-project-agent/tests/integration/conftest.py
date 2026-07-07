"""Fixtures for integration tests against a real local Ollama instance."""

from __future__ import annotations

import json
import urllib.request

import pytest
from langgraph_project_agent import llm
from langgraph_project_agent.config import settings

_PULL_HINT = (
    "Ollama not reachable or model not pulled - for local use: "
    "docker compose up -d && docker compose exec ollama ollama pull llama3.2"
)


@pytest.fixture(scope="session")
def ollama_provider():
    try:
        with urllib.request.urlopen(f"{settings.ollama_base_url}/api/tags", timeout=5) as resp:
            tags = json.load(resp)
        available = {m["name"].split(":")[0] for m in tags.get("models", [])}
        if settings.ollama_model.split(":")[0] not in available:
            pytest.skip(_PULL_HINT)
    except OSError:
        pytest.skip(_PULL_HINT)

    original = settings.llm_provider
    settings.llm_provider = "ollama"
    llm.get_chat_model.cache_clear()
    yield
    settings.llm_provider = original
    llm.get_chat_model.cache_clear()
