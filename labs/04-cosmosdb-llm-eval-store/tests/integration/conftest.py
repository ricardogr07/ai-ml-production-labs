"""Fixtures for integration tests against the CosmosDB Linux emulator or Azure."""

from __future__ import annotations

import contextlib
import os

import pytest
from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosHttpResponseError
from cosmosdb_llm_eval_store.cosmos_repository import CosmosDBEvalStoreRepository

_EMULATOR_URL = "https://localhost:8081"
_EMULATOR_KEY = (
    "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="
)

_URL = os.environ.get("COSMOS_URL", _EMULATOR_URL)
_KEY = os.environ.get("COSMOS_KEY", _EMULATOR_KEY)
_VERIFY_TLS = not _URL.startswith("https://localhost")
_TEST_DB = "llm-eval-test"
_TEST_CONTAINER = "evaluations-test"


@pytest.fixture(scope="session")
def cosmos_repo() -> CosmosDBEvalStoreRepository:  # type: ignore[return]
    try:
        client = CosmosClient(url=_URL, credential=_KEY, connection_verify=_VERIFY_TLS)
        db = client.create_database_if_not_exists(_TEST_DB)
        db.create_container_if_not_exists(
            id=_TEST_CONTAINER,
            partition_key=PartitionKey(path="/experiment_id"),
        )
        yield CosmosDBEvalStoreRepository(client, _TEST_DB, _TEST_CONTAINER)
        with contextlib.suppress(CosmosHttpResponseError):
            client.delete_database(_TEST_DB)
    except Exception:
        pytest.skip("CosmosDB not reachable — for local use: docker compose up -d")
