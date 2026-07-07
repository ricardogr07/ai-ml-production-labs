"""Unit tests for the chat model factory and provider dispatch."""

from __future__ import annotations

import pytest
from langgraph_project_agent import llm, nodes
from langgraph_project_agent.config import settings
from langgraph_project_agent.state import ProjectState


@pytest.fixture(autouse=True)
def clear_model_cache():
    llm.get_chat_model.cache_clear()
    yield
    llm.get_chat_model.cache_clear()


@pytest.mark.unit
def test_factory_raises_for_provider_none():
    with pytest.raises(ValueError, match="none"):
        llm.get_chat_model()


@pytest.mark.unit
def test_factory_returns_configured_chat_ollama(monkeypatch):
    from langchain_ollama import ChatOllama

    monkeypatch.setattr(settings, "llm_provider", "ollama")
    monkeypatch.setattr(settings, "ollama_base_url", "http://example:11434")
    monkeypatch.setattr(settings, "ollama_model", "test-model")
    model = llm.get_chat_model()
    assert isinstance(model, ChatOllama)
    assert model.base_url == "http://example:11434"
    assert model.model == "test-model"


@pytest.mark.unit
def test_factory_returns_configured_chat_anthropic(monkeypatch):
    from langchain_anthropic import ChatAnthropic

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(settings, "llm_provider", "anthropic")
    model = llm.get_chat_model()
    assert isinstance(model, ChatAnthropic)
    assert model.model == "claude-opus-4-8"


@pytest.mark.unit
def test_factory_uses_api_key_from_settings(monkeypatch):
    from pydantic import SecretStr

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(settings, "llm_provider", "anthropic")
    monkeypatch.setattr(settings, "anthropic_api_key", SecretStr("dotenv-key"))
    model = llm.get_chat_model()
    assert model.anthropic_api_key.get_secret_value() == "dotenv-key"


@pytest.mark.unit
def test_nodes_dispatch_to_llm_when_provider_set(monkeypatch):
    sentinel = ProjectState(project_idea="x", project_type="rag_system")
    monkeypatch.setattr(settings, "llm_provider", "ollama")
    monkeypatch.setattr(llm, "llm_classify", lambda _state: sentinel)
    assert nodes.classify_project_type(ProjectState(project_idea="x")) is sentinel


@pytest.mark.unit
def test_nodes_use_heuristics_by_default():
    assert settings.llm_provider == "none"
    result = nodes.classify_project_type(ProjectState(project_idea="a rag pipeline"))
    assert result.project_type == "rag_system"
