from __future__ import annotations

import pytest
from qdrant_client import QdrantClient
from rag_retrieval_strategy_lab.repository import QdrantVectorStoreRepository
from rag_retrieval_strategy_lab.schemas import Document


@pytest.fixture
def repo() -> QdrantVectorStoreRepository:
    client = QdrantClient(":memory:")
    return QdrantVectorStoreRepository(client, "documents", vector_size=3)


@pytest.mark.unit
def test_search_returns_closest_document(repo: QdrantVectorStoreRepository) -> None:
    repo.add(Document(id="a", content="alpha", category="x", embedding=[1.0, 0.0, 0.0]))
    repo.add(Document(id="b", content="beta", category="x", embedding=[0.0, 1.0, 0.0]))

    results = repo.search([1.0, 0.0, 0.0], top_k=1)

    assert len(results) == 1
    assert results[0].doc_id == "a"
    assert results[0].score == pytest.approx(1.0)


@pytest.mark.unit
def test_search_respects_top_k(repo: QdrantVectorStoreRepository) -> None:
    for i in range(5):
        repo.add(Document(id=f"doc-{i}", content=str(i), category="x", embedding=[1.0, 0.0, 0.0]))

    results = repo.search([1.0, 0.0, 0.0], top_k=2)

    assert len(results) == 2


@pytest.mark.unit
def test_search_filtered_excludes_other_categories(repo: QdrantVectorStoreRepository) -> None:
    repo.add(Document(id="a", content="alpha", category="ml", embedding=[1.0, 0.0, 0.0]))
    repo.add(Document(id="b", content="beta", category="cooking", embedding=[1.0, 0.0, 0.0]))

    results = repo.search_filtered([1.0, 0.0, 0.0], "category", "ml", top_k=5)

    assert [r.doc_id for r in results] == ["a"]


@pytest.mark.unit
def test_add_overwrites_duplicate_id(repo: QdrantVectorStoreRepository) -> None:
    repo.add(Document(id="a", content="first", category="x", embedding=[1.0, 0.0, 0.0]))
    repo.add(Document(id="a", content="second", category="x", embedding=[1.0, 0.0, 0.0]))

    results = repo.search([1.0, 0.0, 0.0], top_k=5)

    assert len(results) == 1
    assert results[0].content == "second"
