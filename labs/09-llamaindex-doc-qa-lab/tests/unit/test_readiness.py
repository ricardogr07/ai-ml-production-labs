"""Unit tests for the readiness checks: every failure path is mocked so these
run in CI without live Qdrant or Ollama."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from llamaindex_doc_qa_lab import readiness
from llamaindex_doc_qa_lab.config import settings
from llamaindex_doc_qa_lab.errors import NotReadyError


@pytest.fixture()
def mock_qdrant():
    with patch("llamaindex_doc_qa_lab.readiness.vector_store.make_qdrant_client") as factory:
        instance = MagicMock()
        factory.return_value = instance
        yield instance


class _FakeResponse:
    """Minimal stand-in for the urlopen context manager json.load reads from."""

    def __init__(self, payload: dict) -> None:
        self._data = json.dumps(payload)

    def read(self) -> str:
        return self._data

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None


def _fake_urlopen(payload: dict):
    def _open(*_args: object, **_kwargs: object) -> _FakeResponse:
        return _FakeResponse(payload)

    return _open


@pytest.mark.unit
def test_check_qdrant_missing_collection(mock_qdrant):
    mock_qdrant.collection_exists.return_value = False
    with pytest.raises(NotReadyError, match="does not exist"):
        readiness.check_qdrant()


@pytest.mark.unit
def test_check_qdrant_unnamed_vector(mock_qdrant):
    mock_qdrant.collection_exists.return_value = True
    with (
        patch("llamaindex_doc_qa_lab.readiness.vector_store.named_vector", return_value=None),
        pytest.raises(NotReadyError, match="no named text-dense"),
    ):
        readiness.check_qdrant()


@pytest.mark.unit
def test_check_qdrant_wrong_dimension(mock_qdrant):
    mock_qdrant.collection_exists.return_value = True
    with (
        patch(
            "llamaindex_doc_qa_lab.readiness.vector_store.named_vector",
            return_value=MagicMock(size=768),
        ),
        patch("llamaindex_doc_qa_lab.readiness.embeddings.embedding_dim", return_value=384),
        pytest.raises(NotReadyError, match="dim 768"),
    ):
        readiness.check_qdrant()


@pytest.mark.unit
def test_check_qdrant_embedding_model_fails(mock_qdrant):
    mock_qdrant.collection_exists.return_value = True
    with (
        patch(
            "llamaindex_doc_qa_lab.readiness.vector_store.named_vector",
            return_value=MagicMock(size=384),
        ),
        patch(
            "llamaindex_doc_qa_lab.readiness.embeddings.embedding_dim",
            side_effect=RuntimeError("model weights not found"),
        ),
        pytest.raises(NotReadyError, match="failed to load"),
    ):
        readiness.check_qdrant()


@pytest.mark.unit
def test_check_qdrant_empty_collection(mock_qdrant):
    mock_qdrant.collection_exists.return_value = True
    mock_qdrant.count.return_value = MagicMock(count=0)
    with (
        patch(
            "llamaindex_doc_qa_lab.readiness.vector_store.named_vector",
            return_value=MagicMock(size=384),
        ),
        patch("llamaindex_doc_qa_lab.readiness.embeddings.embedding_dim", return_value=384),
        pytest.raises(NotReadyError, match="is empty"),
    ):
        readiness.check_qdrant()


@pytest.mark.unit
def test_check_qdrant_ok(mock_qdrant):
    mock_qdrant.collection_exists.return_value = True
    mock_qdrant.count.return_value = MagicMock(count=5)
    with (
        patch(
            "llamaindex_doc_qa_lab.readiness.vector_store.named_vector",
            return_value=MagicMock(size=384),
        ),
        patch("llamaindex_doc_qa_lab.readiness.embeddings.embedding_dim", return_value=384),
    ):
        readiness.check_qdrant()  # does not raise


@pytest.mark.unit
def test_check_qdrant_unreachable(mock_qdrant):
    mock_qdrant.collection_exists.side_effect = ConnectionError("connection refused")
    with pytest.raises(NotReadyError, match="not reachable"):
        readiness.check_qdrant()


@pytest.mark.unit
def test_check_llm_ollama_unreachable(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "ollama")
    with (
        patch("urllib.request.urlopen", side_effect=OSError("no route to host")),
        pytest.raises(NotReadyError, match="not reachable"),
    ):
        readiness.check_llm()


@pytest.mark.unit
def test_check_llm_ollama_model_not_pulled(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "ollama")
    monkeypatch.setattr(settings, "ollama_model", "llama3.2")
    with (
        patch("urllib.request.urlopen", _fake_urlopen({"models": [{"name": "other:latest"}]})),
        pytest.raises(NotReadyError, match="not pulled"),
    ):
        readiness.check_llm()


@pytest.mark.unit
def test_check_llm_ollama_ok(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "ollama")
    monkeypatch.setattr(settings, "ollama_model", "llama3.2")
    with patch("urllib.request.urlopen", _fake_urlopen({"models": [{"name": "llama3.2:latest"}]})):
        readiness.check_llm()  # does not raise


@pytest.mark.unit
def test_check_llm_ollama_tagged_model_missing(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "ollama")
    monkeypatch.setattr(settings, "ollama_model", "llama3.2:1b")
    with (
        patch("urllib.request.urlopen", _fake_urlopen({"models": [{"name": "llama3.2:latest"}]})),
        pytest.raises(NotReadyError, match="not pulled"),
    ):
        readiness.check_llm()


@pytest.mark.unit
def test_check_llm_ollama_tagged_model_present(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "ollama")
    monkeypatch.setattr(settings, "ollama_model", "llama3.2:1b")
    with patch("urllib.request.urlopen", _fake_urlopen({"models": [{"name": "llama3.2:1b"}]})):
        readiness.check_llm()  # does not raise


@pytest.mark.unit
def test_check_llm_anthropic_missing_key(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "anthropic")
    monkeypatch.setattr(settings, "anthropic_api_key", None)
    with pytest.raises(NotReadyError, match="ANTHROPIC_API_KEY"):
        readiness.check_llm()


@pytest.mark.unit
def test_readiness_aggregates_failures(mock_qdrant, monkeypatch):
    mock_qdrant.collection_exists.return_value = False
    monkeypatch.setattr(settings, "llm_provider", "anthropic")
    monkeypatch.setattr(settings, "anthropic_api_key", None)
    report = readiness.readiness()
    assert "does not exist" in report["qdrant"]
    assert "ANTHROPIC_API_KEY" in report["llm"]
