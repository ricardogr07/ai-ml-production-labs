"""Integration tests against the CosmosDB emulator (CRUD + cosine fallback)."""

from __future__ import annotations

import uuid

import pytest
from cosmosdb_vector_memory_lab.cosmos_repository import CosmosDBVectorStoreRepository
from cosmosdb_vector_memory_lab.schemas import Document


@pytest.mark.integration
def test_add_and_retrieve(cosmos_repo: CosmosDBVectorStoreRepository) -> None:
    doc = Document(id=str(uuid.uuid4()), content="machine learning", embedding=[1.0, 0.0, 0.0])
    cosmos_repo.add(doc)
    fetched = cosmos_repo.get(doc.id)
    assert fetched is not None
    assert fetched.id == doc.id
    assert fetched.content == doc.content
    assert fetched.embedding == doc.embedding
    cosmos_repo.delete(doc.id)


@pytest.mark.integration
def test_add_overwrites(cosmos_repo: CosmosDBVectorStoreRepository) -> None:
    doc_id = str(uuid.uuid4())
    cosmos_repo.add(Document(id=doc_id, content="first", embedding=[1.0, 0.0, 0.0]))
    cosmos_repo.add(Document(id=doc_id, content="second", embedding=[1.0, 0.0, 0.0]))
    fetched = cosmos_repo.get(doc_id)
    assert fetched is not None
    assert fetched.content == "second"
    cosmos_repo.delete(doc_id)


@pytest.mark.integration
def test_delete(cosmos_repo: CosmosDBVectorStoreRepository) -> None:
    doc = Document(id=str(uuid.uuid4()), content="to delete", embedding=[0.0, 1.0, 0.0])
    cosmos_repo.add(doc)
    cosmos_repo.delete(doc.id)
    assert cosmos_repo.get(doc.id) is None


@pytest.mark.integration
def test_get_nonexistent(cosmos_repo: CosmosDBVectorStoreRepository) -> None:
    assert cosmos_repo.get("does-not-exist-" + str(uuid.uuid4())) is None


@pytest.mark.integration
def test_search_fallback(cosmos_repo: CosmosDBVectorStoreRepository) -> None:
    prefix = str(uuid.uuid4())[:8]
    docs = [
        Document(id=f"{prefix}-a", content="alpha", embedding=[1.0, 0.0, 0.0]),
        Document(id=f"{prefix}-b", content="beta", embedding=[0.0, 1.0, 0.0]),
        Document(id=f"{prefix}-c", content="gamma", embedding=[0.0, 0.0, 1.0]),
    ]
    for d in docs:
        cosmos_repo.add(d)

    results = cosmos_repo.search([1.0, 0.0, 0.0], top_k=1)
    assert len(results) >= 1
    top = results[0]
    assert top.document.id == f"{prefix}-a"
    assert top.score > 0.9
