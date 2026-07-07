#!/usr/bin/env python3
"""
Smoke test for the CosmosDB vector memory store.

Uses hardcoded embeddings (no model download). Validates two paths:
  success path  -- add 3 docs, search, verify ranking
  error path    -- get nonexistent id, verify None (no exception)

Usage:
  uv run python labs/06-cosmosdb-vector-memory-lab/scripts/smoke_test.py
  uv run python labs/06-cosmosdb-vector-memory-lab/scripts/smoke_test.py --target deployed
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import uuid
import warnings

import structlog
from azure.cosmos import CosmosClient, PartitionKey
from cosmosdb_vector_memory_lab.cosmos_repository import CosmosDBVectorStoreRepository
from cosmosdb_vector_memory_lab.schemas import Document

from production_labs_shared.logging import configure_logging
from production_labs_shared.telemetry import timed_operation

logging.getLogger("azure").setLevel(logging.WARNING)
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

_EMULATOR_URL = "https://localhost:8082"
_EMULATOR_KEY = (
    "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="
)


def _build_repo(target: str) -> CosmosDBVectorStoreRepository:
    if target == "local":
        url, key, verify = _EMULATOR_URL, _EMULATOR_KEY, False
        use_vector_index = False
        # ponytail: smoke test uses its own container so its 3-dim toy vectors
        # never collide with seed_data.py's 384-dim demo corpus in the emulator's
        # cosine fallback scan (real Azure containers enforce one fixed dimension,
        # so this only matters for the local, non-indexed path).
        database = "vector-memory-smoke"
        container = "documents-smoke"
    else:
        url = os.environ["COSMOS_URL"]
        key = os.environ["COSMOS_KEY"]
        verify = True
        use_vector_index = True
        database = os.environ.get("COSMOS_DATABASE", "vector-memory")
        container = os.environ.get("COSMOS_CONTAINER", "documents")

    client = CosmosClient(
        url=url, credential=key, connection_verify=verify, enable_endpoint_discovery=verify
    )
    db = client.create_database_if_not_exists(database)
    db.create_container_if_not_exists(
        id=container,
        partition_key=PartitionKey(path="/id"),
    )
    return CosmosDBVectorStoreRepository(
        client, database, container, use_vector_index=use_vector_index
    )


def _success_path(repo: CosmosDBVectorStoreRepository, log: structlog.BoundLogger) -> None:  # type: ignore[type-arg]
    prefix = uuid.uuid4().hex[:8]
    docs = [
        Document(id=f"{prefix}-a", content="machine learning", embedding=[1.0, 0.0, 0.0]),
        Document(id=f"{prefix}-b", content="docker containers", embedding=[0.0, 1.0, 0.0]),
        Document(id=f"{prefix}-c", content="azure devops", embedding=[0.0, 0.0, 1.0]),
    ]
    for doc in docs:
        with timed_operation("add_document", doc_id=doc.id):
            repo.add(doc)
    log.info("smoke.success_path.docs_added", prefix=prefix)

    with timed_operation("search"):
        results = repo.search([1.0, 0.0, 0.0], top_k=1)

    assert len(results) >= 1, f"Expected at least 1 result, got {len(results)}"
    assert results[0].document.id == f"{prefix}-a", (
        f"Expected {prefix}-a as top result, got {results[0].document.id}"
    )
    log.info("smoke.success_path.ok", top_doc=results[0].document.id, score=results[0].score)


def _error_path(repo: CosmosDBVectorStoreRepository, log: structlog.BoundLogger) -> None:  # type: ignore[type-arg]
    missing_id = f"nonexistent-{uuid.uuid4()}"
    with timed_operation("get_missing", doc_id=missing_id):
        result = repo.get(missing_id)

    assert result is None, f"Expected None for missing doc, got {result!r}"
    log.info("smoke.error_path.ok", doc_id=missing_id)


def main() -> int:
    configure_logging()
    log = structlog.get_logger()

    parser = argparse.ArgumentParser(description="Smoke test the CosmosDB vector memory store.")
    parser.add_argument(
        "--target",
        choices=["local", "deployed"],
        default="local",
        help=(
            "'local' uses the CosmosDB emulator (port 8082); "
            "'deployed' reads COSMOS_URL / COSMOS_KEY"
        ),
    )
    args = parser.parse_args()
    log.info("smoke.init", target=args.target)

    try:
        repo = _build_repo(args.target)
    except KeyError as exc:
        log.error("smoke.config_error", missing_env_var=str(exc))
        return 1

    try:
        _success_path(repo, log)
        _error_path(repo, log)
    except AssertionError as exc:
        log.error("smoke.assertion_failed", detail=str(exc))
        return 1

    log.info("smoke.all_paths_passed", target=args.target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
