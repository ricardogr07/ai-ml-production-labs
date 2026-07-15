"""Unit tests for the LLM factory and provider dispatch."""

from __future__ import annotations

import pytest
from llamaindex_doc_qa_lab import llm
from llamaindex_doc_qa_lab.config import settings


@pytest.fixture(autouse=True)
def clear_llm_cache():
    llm.get_llm.cache_clear()
    yield
    llm.get_llm.cache_clear()


@pytest.mark.unit
def test_factory_returns_configured_ollama(monkeypatch):
    from llama_index.llms.ollama import Ollama

    monkeypatch.setattr(settings, "llm_provider", "ollama")
    monkeypatch.setattr(settings, "ollama_base_url", "http://example:11434")
    monkeypatch.setattr(settings, "ollama_model", "test-model")
    model = llm.get_llm()
    assert isinstance(model, Ollama)
    assert model.base_url == "http://example:11434"
    assert model.model == "test-model"
    # regression guard: the llama-index default (30s) is too short for CPU
    # inference plus multi-chunk refine synthesis, and fails as a silent 500.
    assert model.request_timeout >= 180.0


@pytest.mark.unit
def test_factory_returns_configured_anthropic(monkeypatch):
    from llama_index.llms.anthropic import Anthropic

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(settings, "llm_provider", "anthropic")
    model = llm.get_llm()
    assert isinstance(model, Anthropic)
    assert model.model == "claude-opus-4-8"


@pytest.mark.unit
def test_factory_uses_api_key_from_settings(monkeypatch):
    from pydantic import SecretStr

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(settings, "llm_provider", "anthropic")
    monkeypatch.setattr(settings, "anthropic_api_key", SecretStr("dotenv-key"))
    model = llm.get_llm()
    assert model._client.api_key == "dotenv-key"


@pytest.mark.unit
def test_factory_raises_for_unknown_provider(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "bogus")
    with pytest.raises(ValueError, match="bogus"):
        llm.get_llm()
