#!/usr/bin/env python3
"""Run example SQL queries against the CosmosDB eval store and print results."""

from __future__ import annotations

import json
import logging
import os
import sys
import warnings

from azure.cosmos import CosmosClient

logging.getLogger("azure").setLevel(logging.WARNING)
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

_EMULATOR_URL = "https://localhost:8081"
_EMULATOR_KEY = (
    "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="
)


def _build_container() -> object:
    url = os.environ.get("COSMOS_URL", _EMULATOR_URL)
    key = os.environ.get("COSMOS_KEY", _EMULATOR_KEY)
    database = os.environ.get("COSMOS_DATABASE", "llm-eval-store")
    container = os.environ.get("COSMOS_CONTAINER", "evaluations")
    is_emulator = url == _EMULATOR_URL
    client = CosmosClient(url=url, credential=key, connection_verify=not is_emulator)
    return client.get_database_client(database).get_container_client(container)


def _run_query(container: object, label: str, query: str, parameters: list[dict]) -> None:  # type: ignore[type-arg]
    print(f"\n{'=' * 60}")
    print(f"Query: {label}")
    print(f"SQL:   {query}")
    print(f"{'=' * 60}")
    results = list(
        container.query_items(  # type: ignore[attr-defined]
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True,
        )
    )
    if results:
        for item in results:
            item.pop("_rid", None)
            item.pop("_self", None)
            item.pop("_etag", None)
            item.pop("_attachments", None)
            item.pop("_ts", None)
            print(json.dumps(item, indent=2, default=str))
    else:
        print("(no results)")
    print(f"Total: {len(results)} document(s)")


def main() -> int:
    container = _build_container()

    _run_query(
        container,
        label="All evaluation scores for exp-001",
        query=(
            "SELECT * FROM c WHERE c.experiment_id = @experiment_id AND c.document_type = @doc_type"
        ),
        parameters=[
            {"name": "@experiment_id", "value": "exp-001"},
            {"name": "@doc_type", "value": "evaluation_score"},
        ],
    )

    _run_query(
        container,
        label="All prompt runs for exp-001",
        query=(
            "SELECT * FROM c WHERE c.experiment_id = @experiment_id AND c.document_type = @doc_type"
        ),
        parameters=[
            {"name": "@experiment_id", "value": "exp-001"},
            {"name": "@doc_type", "value": "prompt_run"},
        ],
    )

    _run_query(
        container,
        label="Model responses with latency > 200 ms (cross-partition)",
        query=(
            "SELECT c.id, c.experiment_id, c.latency_ms, c.token_count FROM c "
            "WHERE c.document_type = @doc_type "
            "AND c.latency_ms > @threshold"
        ),
        parameters=[
            {"name": "@doc_type", "value": "model_response"},
            {"name": "@threshold", "value": 200},
        ],
    )

    # Cosmos SQL cross-partition aggregates require VALUE syntax; GROUP BY is not supported here.
    print(f"\n{'=' * 60}")
    print("Query: Document counts per type (cross-partition VALUE COUNT)")
    print(f"{'=' * 60}")
    doc_types = ["experiment", "prompt_run", "model_response", "evaluation_score"]
    for doc_type in doc_types:
        results = list(
            container.query_items(  # type: ignore[attr-defined]
                query="SELECT VALUE COUNT(1) FROM c WHERE c.document_type = @doc_type",
                parameters=[{"name": "@doc_type", "value": doc_type}],
                enable_cross_partition_query=True,
            )
        )
        count = results[0] if results else 0
        print(f"  {doc_type:<25} {count} document(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
