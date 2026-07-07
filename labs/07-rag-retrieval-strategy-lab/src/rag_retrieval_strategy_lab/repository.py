"""Vector store repository backed by Qdrant."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from qdrant_client import QdrantClient, models

from rag_retrieval_strategy_lab.schemas import Document, RetrievalResult

_NAMESPACE = uuid.NAMESPACE_DNS


def _point_id(doc_id: str) -> str:
    """Qdrant point IDs must be an unsigned int or a UUID, derive one deterministically."""
    return str(uuid.uuid5(_NAMESPACE, doc_id))


class VectorStoreRepository(ABC):
    @abstractmethod
    def add(self, document: Document) -> None: ...

    @abstractmethod
    def search(self, query_embedding: list[float], top_k: int = 3) -> list[RetrievalResult]: ...

    @abstractmethod
    def search_filtered(
        self,
        query_embedding: list[float],
        filter_key: str,
        filter_value: str,
        top_k: int = 3,
    ) -> list[RetrievalResult]: ...


class QdrantVectorStoreRepository(VectorStoreRepository):
    def __init__(
        self,
        client: QdrantClient,
        collection: str,
        *,
        vector_size: int = 384,
    ) -> None:
        self._client = client
        self._collection = collection
        if not self._client.collection_exists(collection):
            self._client.create_collection(
                collection,
                vectors_config=models.VectorParams(
                    size=vector_size, distance=models.Distance.COSINE
                ),
            )

    def add(self, document: Document) -> None:
        self._client.upsert(
            self._collection,
            points=[
                models.PointStruct(
                    id=_point_id(document.id),
                    vector=document.embedding,
                    payload={
                        "doc_id": document.id,
                        "content": document.content,
                        "category": document.category,
                    },
                )
            ],
        )

    def search(self, query_embedding: list[float], top_k: int = 3) -> list[RetrievalResult]:
        return self._query(query_embedding, top_k, query_filter=None)

    def search_filtered(
        self,
        query_embedding: list[float],
        filter_key: str,
        filter_value: str,
        top_k: int = 3,
    ) -> list[RetrievalResult]:
        query_filter = models.Filter(
            must=[
                models.FieldCondition(key=filter_key, match=models.MatchValue(value=filter_value))
            ]
        )
        return self._query(query_embedding, top_k, query_filter=query_filter)

    def _query(
        self,
        query_embedding: list[float],
        top_k: int,
        query_filter: models.Filter | None,
    ) -> list[RetrievalResult]:
        response = self._client.query_points(
            self._collection,
            query=query_embedding,
            query_filter=query_filter,
            limit=top_k,
        )
        return [
            RetrievalResult(
                doc_id=point.payload["doc_id"],  # type: ignore[index]
                content=point.payload["content"],  # type: ignore[index]
                score=point.score,
            )
            for point in response.points
        ]
