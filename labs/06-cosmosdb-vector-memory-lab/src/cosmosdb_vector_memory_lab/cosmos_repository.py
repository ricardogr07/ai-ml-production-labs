"""Azure Cosmos DB implementation of the vector store repository."""

from __future__ import annotations

import contextlib

from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosResourceNotFoundError

from cosmosdb_vector_memory_lab.memory import _cosine_similarity
from cosmosdb_vector_memory_lab.repository import VectorStoreRepository
from cosmosdb_vector_memory_lab.schemas import Document, SearchResult


class CosmosDBVectorStoreRepository(VectorStoreRepository):
    def __init__(
        self,
        client: CosmosClient,
        database: str,
        container: str,
        *,
        use_vector_index: bool = True,
    ) -> None:
        self._container = client.get_database_client(database).get_container_client(container)
        self._use_vector_index = use_vector_index

    def add(self, document: Document) -> None:
        self._container.upsert_item(document.model_dump(mode="json"))

    def get(self, document_id: str) -> Document | None:
        try:
            item = self._container.read_item(item=document_id, partition_key=document_id)
            return Document(**item)
        except CosmosResourceNotFoundError:
            return None

    def delete(self, document_id: str) -> None:
        with contextlib.suppress(CosmosResourceNotFoundError):
            self._container.delete_item(item=document_id, partition_key=document_id)

    def search(self, query_embedding: list[float], top_k: int = 3) -> list[SearchResult]:
        if self._use_vector_index:
            return self._search_vector_index(query_embedding, top_k)
        return self._search_cosine_fallback(query_embedding, top_k)

    def _search_vector_index(self, query_embedding: list[float], top_k: int) -> list[SearchResult]:
        items = list(
            self._container.query_items(
                query=(
                    "SELECT TOP @k c.id, c.content, c.source, c.embedding, c.metadata, "
                    "VectorDistance(c.embedding, @vec) AS score "
                    "FROM c "
                    "ORDER BY VectorDistance(c.embedding, @vec)"
                ),
                parameters=[
                    {"name": "@k", "value": top_k},
                    {"name": "@vec", "value": query_embedding},
                ],
                enable_cross_partition_query=True,
            )
        )
        return [
            SearchResult(
                document=Document(**{k: v for k, v in item.items() if k != "score"}),
                score=item["score"],
            )
            for item in items
        ]

    def _search_cosine_fallback(
        self, query_embedding: list[float], top_k: int
    ) -> list[SearchResult]:
        all_items = list(
            self._container.query_items(
                query="SELECT * FROM c",
                enable_cross_partition_query=True,
            )
        )
        scored = [
            SearchResult(
                document=Document(**item),
                score=_cosine_similarity(query_embedding, item.get("embedding") or []),
            )
            for item in all_items
            if item.get("embedding")
        ]
        return sorted(scored, key=lambda r: r.score, reverse=True)[:top_k]
