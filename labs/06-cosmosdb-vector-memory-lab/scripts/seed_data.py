#!/usr/bin/env python3
"""
Seed the CosmosDB vector memory store with sample documents.

Downloads the all-MiniLM-L6-v2 model (~90 MB on first run), embeds a small
corpus, upserts each document into the store, then runs a demo query.

Usage:
  uv run python labs/06-cosmosdb-vector-memory-lab/scripts/seed_data.py
  uv run python labs/06-cosmosdb-vector-memory-lab/scripts/seed_data.py --target deployed
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import warnings
from pathlib import Path

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

_CORPUS_PATH = Path(__file__).parent.parent / "data" / "wikipedia_corpus.json"


def _load_corpus() -> list[tuple[str, str, str]]:
    docs = json.loads(_CORPUS_PATH.read_text(encoding="utf-8"))
    return [(doc["id"], doc["content"], doc["source"]) for doc in docs]


_DEMO_QUERY = "how do vector databases retrieve similar documents"


def _build_repo(target: str) -> tuple[CosmosDBVectorStoreRepository, bool]:
    if target == "local":
        url, key, verify = _EMULATOR_URL, _EMULATOR_KEY, False
        use_vector_index = False
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
    repo = CosmosDBVectorStoreRepository(
        client, database, container, use_vector_index=use_vector_index
    )
    return repo, use_vector_index


def main() -> int:
    configure_logging()
    log = structlog.get_logger()

    parser = argparse.ArgumentParser(description="Seed the CosmosDB vector memory store.")
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
    log.info("seed.init", target=args.target)

    try:
        repo, use_vector_index = _build_repo(args.target)
    except KeyError as exc:
        log.error("seed.config_error", missing_env_var=str(exc))
        return 1

    log.info("seed.loading_model", model="all-MiniLM-L6-v2")
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("all-MiniLM-L6-v2")

    corpus = _load_corpus()
    texts = [text for _, text, _ in corpus]
    with timed_operation("embed_corpus", doc_count=len(texts)):
        embeddings = model.encode(texts, normalize_embeddings=True).tolist()

    for (doc_id, content, source), embedding in zip(corpus, embeddings, strict=True):
        doc = Document(id=doc_id, content=content, source=source, embedding=embedding)
        with timed_operation("add_document", doc_id=doc_id):
            repo.add(doc)
        log.info("seed.document_added", doc_id=doc_id, source=source)

    log.info("seed.running_demo_query", query=_DEMO_QUERY)
    with timed_operation("search", query=_DEMO_QUERY):
        query_embedding = model.encode([_DEMO_QUERY], normalize_embeddings=True).tolist()[0]
        results = repo.search(query_embedding, top_k=3)

    log.info("seed.search_results", count=len(results))
    for rank, result in enumerate(results, 1):
        log.info(
            "seed.result",
            rank=rank,
            doc_id=result.document.id,
            content=result.document.content,
            score=round(result.score, 4),
        )

    log.info("seed.complete", use_vector_index=use_vector_index)
    return 0


if __name__ == "__main__":
    sys.exit(main())
