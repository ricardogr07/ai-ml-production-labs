from __future__ import annotations

import pytest
from qdrant_client import QdrantClient
from rag_retrieval_strategy_lab.repository import QdrantVectorStoreRepository
from rag_retrieval_strategy_lab.schemas import Document
from rag_retrieval_strategy_lab.strategies import (
    expanded_query_search,
    metadata_filtered_search,
    naive_search,
    reranked_search,
)


@pytest.fixture
def repo() -> QdrantVectorStoreRepository:
    client = QdrantClient(":memory:")
    store = QdrantVectorStoreRepository(client, "documents", vector_size=3)
    store.add(Document(id="a", content="alpha topic", category="x", embedding=[1.0, 0.0, 0.0]))
    store.add(Document(id="b", content="beta topic", category="y", embedding=[0.0, 1.0, 0.0]))
    store.add(Document(id="c", content="gamma topic", category="x", embedding=[0.9, 0.1, 0.0]))
    return store


@pytest.mark.unit
def test_naive_search_ranks_by_similarity(repo: QdrantVectorStoreRepository) -> None:
    results = naive_search(repo, [1.0, 0.0, 0.0], top_k=2)

    assert [r.doc_id for r in results] == ["a", "c"]


@pytest.mark.unit
def test_metadata_filtered_search_excludes_other_categories(
    repo: QdrantVectorStoreRepository,
) -> None:
    results = metadata_filtered_search(repo, [1.0, 0.0, 0.0], "category", "y", top_k=5)

    assert [r.doc_id for r in results] == ["b"]


@pytest.mark.unit
def test_reranked_search_reorders_by_rerank_score(repo: QdrantVectorStoreRepository) -> None:
    # Stub reranker that reverses the naive ranking, proving the strategy
    # actually uses the rerank scores rather than passing candidates through.
    def reverse_rerank(_query: str, documents: list[str]) -> list[float]:
        return list(range(len(documents)))

    results = reranked_search(
        repo, "query", [1.0, 0.0, 0.0], reverse_rerank, top_k=2, candidate_k=3
    )

    assert [r.doc_id for r in results] == ["b", "c"]


@pytest.mark.unit
def test_expanded_query_search_uses_expanded_embedding(repo: QdrantVectorStoreRepository) -> None:
    calls: list[str] = []

    def embed_fn(text: str) -> list[float]:
        calls.append(text)
        return [1.0, 0.0, 0.0]

    results = expanded_query_search(repo, "space objects", embed_fn, top_k=1)

    assert calls[0] == "space objects black hole exoplanet milky way supernova neutron star"
    assert results[0].doc_id == "a"
