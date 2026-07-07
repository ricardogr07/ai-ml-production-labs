"""Abstract repository and in-memory implementation for vector storage."""

from __future__ import annotations

from abc import ABC, abstractmethod

from cosmosdb_vector_memory_lab.memory import _cosine_similarity
from cosmosdb_vector_memory_lab.schemas import Document, SearchResult


class VectorStoreRepository(ABC):
    @abstractmethod
    def add(self, document: Document) -> None: ...

    @abstractmethod
    def search(self, query_embedding: list[float], top_k: int = 3) -> list[SearchResult]: ...

    @abstractmethod
    def get(self, document_id: str) -> Document | None: ...

    @abstractmethod
    def delete(self, document_id: str) -> None: ...


class InMemoryVectorStoreRepository(VectorStoreRepository):
    def __init__(self) -> None:
        self._store: dict[str, Document] = {}

    def add(self, document: Document) -> None:
        self._store[document.id] = document

    def get(self, document_id: str) -> Document | None:
        return self._store.get(document_id)

    def delete(self, document_id: str) -> None:
        self._store.pop(document_id, None)

    def search(self, query_embedding: list[float], top_k: int = 3) -> list[SearchResult]:
        scored = [
            SearchResult(document=doc, score=_cosine_similarity(query_embedding, doc.embedding))
            for doc in self._store.values()
            if doc.embedding
        ]
        return sorted(scored, key=lambda r: r.score, reverse=True)[:top_k]
