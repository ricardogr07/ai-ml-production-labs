"""E2E test: DiskANN vector search against real Azure CosmosDB."""

from __future__ import annotations

import contextlib
import os
import uuid

import pytest
from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosHttpResponseError
from cosmosdb_vector_memory_lab.cosmos_repository import CosmosDBVectorStoreRepository
from cosmosdb_vector_memory_lab.schemas import Document

_DIMS = 384


@pytest.mark.e2e
def test_vector_search_azure() -> None:
    url = os.environ.get("COSMOS_URL", "")
    key = os.environ.get("COSMOS_KEY", "")
    if not url or not key:
        pytest.skip("COSMOS_URL / COSMOS_KEY not set — skipping Azure e2e")

    database = os.environ.get("COSMOS_DATABASE", "vector-memory")
    container_id = f"e2e-test-{uuid.uuid4().hex[:8]}"

    client = CosmosClient(url=url, credential=key)
    db = client.create_database_if_not_exists(database)

    vector_embedding_policy = {
        "vectorEmbeddings": [
            {
                "path": "/embedding",
                "dataType": "float32",
                "dimensions": _DIMS,
                "distanceFunction": "cosine",
            }
        ]
    }
    indexing_policy = {"vectorIndexes": [{"path": "/embedding", "type": "diskANN"}]}

    db.create_container_if_not_exists(
        id=container_id,
        partition_key=PartitionKey(path="/id"),
        vector_embedding_policy=vector_embedding_policy,
        indexing_policy=indexing_policy,
    )

    try:
        repo = CosmosDBVectorStoreRepository(client, database, container_id, use_vector_index=True)

        def _unit(pos: int) -> list[float]:
            v = [0.0] * _DIMS
            v[pos] = 1.0
            return v

        docs = [
            Document(id="e2e-1", content="machine learning", embedding=_unit(0)),
            Document(id="e2e-2", content="docker containers", embedding=_unit(1)),
            Document(id="e2e-3", content="azure devops", embedding=_unit(2)),
        ]
        for doc in docs:
            repo.add(doc)

        results = repo.search(_unit(0), top_k=1)
        assert len(results) == 1
        assert results[0].document.id == "e2e-1"
    finally:
        with contextlib.suppress(CosmosHttpResponseError):
            db.delete_container(container_id)
