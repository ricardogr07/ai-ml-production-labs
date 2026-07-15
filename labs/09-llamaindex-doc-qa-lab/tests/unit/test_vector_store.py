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
    monkeypatch.setattr(settings, "qdrant_collection", "test-collection")

    store = vector_store.get_vector_store()

    assert isinstance(store, QdrantVectorStore)
    assert store.collection_name == "test-collection"
    mock_cls.assert_called_once_with(url="http://example:6333")


@pytest.mark.unit
@pytest.mark.usefixtures("mock_qdrant_client")
def test_get_vector_store_is_cached():
    assert vector_store.get_vector_store() is vector_store.get_vector_store()
