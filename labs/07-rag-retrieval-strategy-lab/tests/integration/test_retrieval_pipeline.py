"""End-to-end integration tests: real embeddings, real Qdrant, real cross-encoder."""

from __future__ import annotations

import pytest
from rag_retrieval_strategy_lab.repository import QdrantVectorStoreRepository
from rag_retrieval_strategy_lab.reranker import Reranker
from rag_retrieval_strategy_lab.schemas import Document
from rag_retrieval_strategy_lab.strategies import (
    expanded_query_search,
    metadata_filtered_search,
    naive_search,
    reranked_search,
)

_DOCS = [
    ("doc-a", "Machine learning is a field of artificial intelligence.", "ml"),
    ("doc-b", "Sourdough bread is leavened with wild yeast and bacteria.", "cooking"),
    ("doc-c", "The Roman Empire dominated the Mediterranean for centuries.", "history"),
    ("doc-d", "A black hole's gravity is so strong that light cannot escape.", "astronomy"),
]


@pytest.fixture(scope="module")
def seeded_repo(qdrant_repo: QdrantVectorStoreRepository, embedding_model):  # type: ignore[no-untyped-def]
    texts = [content for _, content, _ in _DOCS]
    embeddings = embedding_model.encode(texts, normalize_embeddings=True).tolist()
    for (doc_id, content, category), embedding in zip(_DOCS, embeddings, strict=True):
        qdrant_repo.add(
            Document(id=doc_id, content=content, category=category, embedding=embedding)
        )
    return qdrant_repo


@pytest.mark.integration
def test_naive_search_finds_relevant_document(seeded_repo, embedding_model) -> None:  # type: ignore[no-untyped-def]
    query_embedding = embedding_model.encode(
        ["neural networks and AI"], normalize_embeddings=True
    ).tolist()[0]

    results = naive_search(seeded_repo, query_embedding, top_k=1)

    assert results[0].doc_id == "doc-a"


@pytest.mark.integration
def test_metadata_filtered_search_restricts_to_category(seeded_repo, embedding_model) -> None:  # type: ignore[no-untyped-def]
    query_embedding = embedding_model.encode(
        ["ancient civilizations"], normalize_embeddings=True
    ).tolist()[0]

    results = metadata_filtered_search(seeded_repo, query_embedding, "category", "cooking", top_k=5)

    assert all(r.doc_id == "doc-b" for r in results)


@pytest.mark.integration
def test_reranked_search_returns_sensible_top_result(
    seeded_repo,
    embedding_model,
    reranker: Reranker,  # type: ignore[no-untyped-def]
) -> None:
    query = "space and black holes"
    query_embedding = embedding_model.encode([query], normalize_embeddings=True).tolist()[0]

    results = reranked_search(
        seeded_repo, query, query_embedding, reranker.score, top_k=1, candidate_k=4
    )

    assert results[0].doc_id == "doc-d"


@pytest.mark.integration
def test_expanded_query_search_returns_sensible_top_result(
    seeded_repo,
    embedding_model,  # type: ignore[no-untyped-def]
) -> None:
    def embed_fn(text: str) -> list[float]:
        return embedding_model.encode([text], normalize_embeddings=True).tolist()[0]  # type: ignore[no-any-return]

    results = expanded_query_search(seeded_repo, "How is AI trained?", embed_fn, top_k=1)

    assert results[0].doc_id == "doc-a"
