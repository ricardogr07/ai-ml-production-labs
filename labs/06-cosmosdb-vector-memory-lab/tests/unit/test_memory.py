from __future__ import annotations

import pytest

from cosmosdb_vector_memory_lab.memory import InMemoryVectorStore
from cosmosdb_vector_memory_lab.schemas import Document


@pytest.fixture
def store() -> InMemoryVectorStore:
    s = InMemoryVectorStore()
    s.add(Document(id="1", content="FastAPI tutorial", embedding=[1.0, 0.0, 0.0]))
    s.add(Document(id="2", content="Docker guide", embedding=[0.0, 1.0, 0.0]))
    s.add(Document(id="3", content="Azure deployment", embedding=[0.0, 0.0, 1.0]))
    return s


@pytest.mark.unit
def test_search_returns_closest_document(store: InMemoryVectorStore) -> None:
    results = store.search([1.0, 0.0, 0.0], top_k=1)

    assert len(results) == 1
    assert results[0].document.id == "1"
    assert results[0].score > 0.9


@pytest.mark.unit
def test_search_respects_top_k(store: InMemoryVectorStore) -> None:
    results = store.search([1.0, 0.0, 0.0], top_k=2)

    assert len(results) == 2


@pytest.mark.unit
def test_search_returns_ranked_by_score(store: InMemoryVectorStore) -> None:
    results = store.search([1.0, 0.5, 0.0], top_k=3)

    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)
