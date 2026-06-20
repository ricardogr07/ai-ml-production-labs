"""Retrieval strategy implementations for the RAG lab."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RetrievalResult:
    doc_id: str
    content: str
    score: float


def naive_search(
    query_embedding: list[float],
    corpus: list[dict[str, object]],
    top_k: int = 3,
) -> list[RetrievalResult]:
    """Brute-force cosine similarity over the whole corpus."""
    import math

    def cosine(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(x * x for x in b))
        return dot / norm if norm else 0.0

    scored = [
        RetrievalResult(
            doc_id=str(doc["id"]),
            content=str(doc["content"]),
            score=cosine(query_embedding, list(doc["embedding"])),  # type: ignore[arg-type]
        )
        for doc in corpus
    ]
    return sorted(scored, key=lambda r: r.score, reverse=True)[:top_k]


def metadata_filtered_search(
    query_embedding: list[float],
    corpus: list[dict[str, object]],
    filter_key: str,
    filter_value: str,
    top_k: int = 3,
) -> list[RetrievalResult]:
    """Filter by metadata before similarity ranking."""
    filtered = [doc for doc in corpus if doc.get(filter_key) == filter_value]
    return naive_search(query_embedding, filtered, top_k=top_k)
