"""Qdrant vector store factory, shared by ingestion and query."""

from __future__ import annotations

from functools import lru_cache

from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from llamaindex_doc_qa_lab.config import settings


@lru_cache(maxsize=1)
def get_vector_store() -> QdrantVectorStore:
    client = QdrantClient(url=settings.qdrant_url)
    return QdrantVectorStore(client=client, collection_name=settings.qdrant_collection)
