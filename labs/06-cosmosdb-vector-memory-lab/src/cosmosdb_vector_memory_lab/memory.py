"""In-memory vector store for local development and testing."""

from __future__ import annotations

import math

from cosmosdb_vector_memory_lab.schemas import Document, SearchResult


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class InMemoryVectorStore:
    def __init__(self) -> None:
        self._documents: list[Document] = []

    def add(self, document: Document) -> None:
        self._documents.append(document)

    def search(self, query_embedding: list[float], top_k: int = 3) -> list[SearchResult]:
        scored = [
            SearchResult(document=doc, score=_cosine_similarity(query_embedding, doc.embedding))
            for doc in self._documents
            if doc.embedding
        ]
        return sorted(scored, key=lambda r: r.score, reverse=True)[:top_k]
