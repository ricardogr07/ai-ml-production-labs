"""Retrieval quality metrics for the RAG strategy lab."""

from __future__ import annotations

from rag_retrieval_strategy_lab.schemas import RetrievalResult


def recall_at_k(retrieved: list[RetrievalResult], relevant_ids: set[str], k: int) -> float:
    """Fraction of relevant documents found in the top-k results."""
    if not relevant_ids:
        return 0.0
    top_ids = {r.doc_id for r in retrieved[:k]}
    return len(top_ids & relevant_ids) / len(relevant_ids)


def mean_reciprocal_rank(retrieved: list[RetrievalResult], relevant_ids: set[str]) -> float:
    """Reciprocal rank of the first relevant document in the result list."""
    for rank, result in enumerate(retrieved, start=1):
        if result.doc_id in relevant_ids:
            return 1.0 / rank
    return 0.0
