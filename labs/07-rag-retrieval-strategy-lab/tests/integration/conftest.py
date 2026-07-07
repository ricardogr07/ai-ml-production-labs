"""Fixtures for integration tests against a real local Qdrant instance and
the real sentence-transformers/cross-encoder models."""

from __future__ import annotations

import os

import pytest
from qdrant_client import QdrantClient
from rag_retrieval_strategy_lab.repository import QdrantVectorStoreRepository
from rag_retrieval_strategy_lab.reranker import Reranker

_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
_TEST_COLLECTION = "documents-test"


@pytest.fixture(scope="session")
def qdrant_repo() -> QdrantVectorStoreRepository:  # type: ignore[return]
    try:
        client = QdrantClient(url=_URL, timeout=5)
        client.get_collections()
        if client.collection_exists(_TEST_COLLECTION):
            client.delete_collection(_TEST_COLLECTION)
        yield QdrantVectorStoreRepository(client, _TEST_COLLECTION, vector_size=384)
        client.delete_collection(_TEST_COLLECTION)
    except Exception:
        pytest.skip("Qdrant not reachable — for local use: docker compose up -d")


@pytest.fixture(scope="session")
def embedding_model():  # type: ignore[no-untyped-def]
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("all-MiniLM-L6-v2")


@pytest.fixture(scope="session")
def reranker() -> Reranker:
    return Reranker()
