"""Unit tests for the Qdrant vector store factory.

QdrantVectorStore's constructor makes a live "does this collection exist"
call against its client, so the QdrantClient itself is mocked here rather
than pointed at a real server - these tests only pin down wiring.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llamaindex_doc_qa_lab import vector_store
from llamaindex_doc_qa_lab.config import settings


@pytest.fixture(autouse=True)
def clear_vector_store_cache():
    vector_store.get_vector_store.cache_clear()
    yield
    vector_store.get_vector_store.cache_clear()


@pytest.fixture()
def mock_qdrant_client():
    with patch("llamaindex_doc_qa_lab.vector_store.QdrantClient") as mock_cls:
        instance = MagicMock()
        instance.collection_exists.return_value = False
        mock_cls.return_value = instance
        yield mock_cls, instance


@pytest.mark.unit
def test_get_vector_store_wires_settings(monkeypatch, mock_qdrant_client):
    mock_cls, _ = mock_qdrant_client
    monkeypatch.setattr(settings, "qdrant_url", "http://example:6333")
    monkeypatch.setattr(settings, "qdrant_api_key", None)
    monkeypatch.setattr(settings, "qdrant_collection", "test-collection")

    store = vector_store.get_vector_store()

    assert isinstance(store, QdrantVectorStore)
    assert store.collection_name == "test-collection"
    mock_cls.assert_called_once_with(url="http://example:6333", api_key=None, timeout=None)


@pytest.mark.unit
@pytest.mark.usefixtures("mock_qdrant_client")
def test_get_vector_store_is_cached():
    assert vector_store.get_vector_store() is vector_store.get_vector_store()


@pytest.mark.unit
def test_make_qdrant_client_threads_api_key(monkeypatch, mock_qdrant_client):
    from pydantic import SecretStr

    mock_cls, _ = mock_qdrant_client
    monkeypatch.setattr(settings, "qdrant_url", "http://example:6333")
    monkeypatch.setattr(settings, "qdrant_api_key", SecretStr("s3cret"))

    vector_store.make_qdrant_client(timeout=5)

    mock_cls.assert_called_once_with(url="http://example:6333", api_key="s3cret", timeout=5)


@pytest.mark.unit
def test_ensure_collection_creates_named_vector():
    client = MagicMock()
    client.collection_exists.return_value = False
    status = vector_store.ensure_collection(client, "docs", 384)
    assert status == "created"
    _, kwargs = client.create_collection.call_args
    vectors_config = kwargs["vectors_config"]
    assert "text-dense" in vectors_config
    assert vectors_config["text-dense"].size == 384


@pytest.mark.unit
def test_ensure_collection_validates_matching_schema():
    client = MagicMock()
    client.collection_exists.return_value = True
    with patch("llamaindex_doc_qa_lab.vector_store.named_vector", return_value=MagicMock(size=384)):
        status = vector_store.ensure_collection(client, "docs", 384)
    assert status == "validated"
    client.create_collection.assert_not_called()


@pytest.mark.unit
def test_ensure_collection_rejects_mismatched_dim():
    client = MagicMock()
    client.collection_exists.return_value = True
    with (
        patch("llamaindex_doc_qa_lab.vector_store.named_vector", return_value=MagicMock(size=768)),
        pytest.raises(SystemExit, match="incompatible vector schema"),
    ):
        vector_store.ensure_collection(client, "docs", 384)


@pytest.mark.unit
def test_ensure_collection_rejects_unnamed_vector():
    client = MagicMock()
    client.collection_exists.return_value = True
    with (
        patch("llamaindex_doc_qa_lab.vector_store.named_vector", return_value=None),
        pytest.raises(SystemExit, match="incompatible vector schema"),
    ):
        vector_store.ensure_collection(client, "docs", 384)


@pytest.mark.unit
def test_ensure_collection_recreate_drops_then_creates():
    client = MagicMock()
    client.collection_exists.return_value = True
    status = vector_store.ensure_collection(client, "docs", 384, recreate=True)
    assert status == "recreated"
    client.delete_collection.assert_called_once_with("docs")
    client.create_collection.assert_called_once()
