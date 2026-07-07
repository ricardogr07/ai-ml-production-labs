"""Retrieval strategy implementations for the RAG lab."""

from __future__ import annotations

from collections.abc import Callable

from rag_retrieval_strategy_lab.query_expansion import expand_query
from rag_retrieval_strategy_lab.repository import VectorStoreRepository
from rag_retrieval_strategy_lab.schemas import RetrievalResult


def naive_search(
    repo: VectorStoreRepository, query_embedding: list[float], top_k: int = 3
) -> list[RetrievalResult]:
    """Brute-force cosine similarity over the whole corpus."""
    return repo.search(query_embedding, top_k=top_k)


def metadata_filtered_search(
    repo: VectorStoreRepository,
    query_embedding: list[float],
    filter_key: str,
    filter_value: str,
    top_k: int = 3,
) -> list[RetrievalResult]:
    """Filter by metadata before similarity ranking."""
    return repo.search_filtered(query_embedding, filter_key, filter_value, top_k=top_k)


def reranked_search(
    repo: VectorStoreRepository,
    query_text: str,
    query_embedding: list[float],
    rerank_fn: Callable[[str, list[str]], list[float]],
    top_k: int = 3,
    candidate_k: int = 10,
) -> list[RetrievalResult]:
    """Similarity search for candidates, then rerank with a cross-encoder."""
    candidates = repo.search(query_embedding, top_k=candidate_k)
    if not candidates:
        return []
    scores = rerank_fn(query_text, [c.content for c in candidates])
    reranked = [
        RetrievalResult(doc_id=c.doc_id, content=c.content, score=score)
        for c, score in zip(candidates, scores, strict=True)
    ]
    return sorted(reranked, key=lambda r: r.score, reverse=True)[:top_k]


def expanded_query_search(
    repo: VectorStoreRepository,
    query_text: str,
    embed_fn: Callable[[str], list[float]],
    top_k: int = 3,
) -> list[RetrievalResult]:
    """Expand the query with related terms before embedding and searching."""
    expanded = expand_query(query_text)
    return repo.search(embed_fn(expanded), top_k=top_k)
