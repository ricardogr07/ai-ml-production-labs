"""Qdrant vector store factory and collection schema helpers.

QdrantVectorStore upserts and queries a NAMED dense vector
(DEFAULT_DENSE_VECTOR_NAME, "text-dense"), but its non-hybrid auto-create makes
an UNNAMED vector, so a later from_vector_store query fails with "Not existing
vector name error: text-dense". `ensure_collection` creates the collection with
the named vector so seed, upsert, and query agree; `named_vector` exposes the
named vector's params for readiness checks.
"""

from __future__ import annotations

from functools import lru_cache

from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.vector_stores.qdrant.base import DEFAULT_DENSE_VECTOR_NAME
from qdrant_client import QdrantClient
from qdrant_client import models as qmodels

from llamaindex_doc_qa_lab.config import settings


def make_qdrant_client(timeout: int | None = None) -> QdrantClient:
    """Build a QdrantClient with the configured URL and optional API key. Every
    Qdrant connection (store, seed, readiness) goes through here so auth is
    threaded in one place; local compose is loopback and needs no key."""
    api_key = settings.qdrant_api_key.get_secret_value() if settings.qdrant_api_key else None
    return QdrantClient(url=settings.qdrant_url, api_key=api_key, timeout=timeout)


@lru_cache(maxsize=1)
def get_vector_store() -> QdrantVectorStore:
    return QdrantVectorStore(
        client=make_qdrant_client(), collection_name=settings.qdrant_collection
    )


def named_vector(client: QdrantClient, collection: str) -> qmodels.VectorParams | None:
    """Return the params of the DEFAULT_DENSE_VECTOR_NAME vector, or None if the
    collection stores an unnamed vector (the pre-fix schema) or lacks that name."""
    vectors = client.get_collection(collection).config.params.vectors
    return vectors.get(DEFAULT_DENSE_VECTOR_NAME) if isinstance(vectors, dict) else None


def ensure_collection(
    client: QdrantClient, collection: str, dim: int, *, recreate: bool = False
) -> str:
    """Create the collection with the named dense vector, or validate an existing
    one. Returns "created", "recreated", or "validated". Raises SystemExit when an
    existing collection has an incompatible schema (unnamed vector or wrong dim),
    so a stale collection is not silently filled with unqueryable points."""
    existed = client.collection_exists(collection)
    recreated = False
    if recreate and existed:
        client.delete_collection(collection)
        existed = False
        recreated = True

    if existed:
        params = named_vector(client, collection)
        if params is None or params.size != dim:
            raise SystemExit(
                f"Collection {collection!r} has an incompatible vector schema "
                f"(need a named {DEFAULT_DENSE_VECTOR_NAME!r} vector at dim {dim}). "
                "Re-run with --recreate to rebuild it."
            )
        return "validated"

    client.create_collection(
        collection,
        vectors_config={
            DEFAULT_DENSE_VECTOR_NAME: qmodels.VectorParams(
                size=dim, distance=qmodels.Distance.COSINE
            )
        },
    )
    return "recreated" if recreated else "created"
