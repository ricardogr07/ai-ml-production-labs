from __future__ import annotations

import pytest
from cosmosdb_vector_memory_lab.repository import InMemoryVectorStoreRepository
from cosmosdb_vector_memory_lab.schemas import Document


@pytest.fixture
def repo() -> InMemoryVectorStoreRepository:
    r = InMemoryVectorStoreRepository()
    r.add(Document(id="1", content="FastAPI tutorial", embedding=[1.0, 0.0, 0.0]))
    r.add(Document(id="2", content="Docker guide", embedding=[0.0, 1.0, 0.0]))
    r.add(Document(id="3", content="Azure deployment", embedding=[0.0, 0.0, 1.0]))
    return r


@pytest.mark.unit
def test_add_and_get() -> None:
    repo = InMemoryVectorStoreRepository()
    doc = Document(id="x", content="hello", embedding=[1.0, 0.0])
    repo.add(doc)
    assert repo.get("x") == doc


@pytest.mark.unit
def test_get_missing() -> None:
    repo = InMemoryVectorStoreRepository()
    assert repo.get("nonexistent") is None


@pytest.mark.unit
def test_delete(repo: InMemoryVectorStoreRepository) -> None:
    repo.delete("1")
    assert repo.get("1") is None


@pytest.mark.unit
def test_delete_nonexistent_is_safe() -> None:
    repo = InMemoryVectorStoreRepository()
    repo.delete("ghost")  # should not raise


@pytest.mark.unit
def test_add_overwrites_duplicate_id() -> None:
    repo = InMemoryVectorStoreRepository()
    repo.add(Document(id="dup", content="first", embedding=[1.0, 0.0]))
    repo.add(Document(id="dup", content="second", embedding=[1.0, 0.0]))
    assert repo.get("dup") is not None
    assert repo.get("dup").content == "second"  # type: ignore[union-attr]


@pytest.mark.unit
def test_search_returns_closest_document(repo: InMemoryVectorStoreRepository) -> None:
    results = repo.search([1.0, 0.0, 0.0], top_k=1)
    assert len(results) == 1
    assert results[0].document.id == "1"
    assert results[0].score > 0.9


@pytest.mark.unit
def test_search_ranked(repo: InMemoryVectorStoreRepository) -> None:
    results = repo.search([1.0, 0.5, 0.0], top_k=3)
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.unit
def test_search_empty_store() -> None:
    repo = InMemoryVectorStoreRepository()
    assert repo.search([1.0, 0.0]) == []
