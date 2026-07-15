#!/usr/bin/env python3
"""
Ingest the committed Wikipedia corpus into Qdrant: chunk, embed, and upsert.

Run this by hand after `docker compose up -d` (or against a deployed Qdrant
by setting QDRANT_URL), before the app can answer any /query requests.

Usage:
  uv run --frozen --package llamaindex-doc-qa-lab python \
    labs/09-llamaindex-doc-qa-lab/scripts/seed_data.py [--recreate]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import structlog
from llama_index.core import Document, StorageContext, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llamaindex_doc_qa_lab import embeddings, vector_store
from llamaindex_doc_qa_lab.config import settings

from production_labs_shared.logging import configure_logging
from production_labs_shared.telemetry import timed_operation

_CORPUS = Path(__file__).parent.parent / "data" / "wikipedia_corpus.json"


def main() -> int:
    configure_logging()
    log = structlog.get_logger()

    parser = argparse.ArgumentParser(description="Seed Qdrant with the Wikipedia corpus.")
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Drop and recreate the Qdrant collection before seeding.",
    )
    args = parser.parse_args()

    embed_model = embeddings.get_embedding_model()
    dim = embeddings.embedding_dim()
    client = vector_store.make_qdrant_client()

    # Create the collection with the named "text-dense" vector (or validate an
    # existing one, failing fast on a mismatched schema); see vector_store.
    status = vector_store.ensure_collection(
        client, settings.qdrant_collection, dim, recreate=args.recreate
    )
    log.info(f"seed.collection_{status}", collection=settings.qdrant_collection, dim=dim)

    records = json.loads(_CORPUS.read_text(encoding="utf-8"))
    documents = [
        Document(
            text=record["content"],
            id_=record["id"],
            metadata={
                "title": record["title"],
                "category": record["category"],
                "source": record["title"],
            },
        )
        for record in records
    ]
    log.info("seed.documents_loaded", count=len(documents))

    storage_context = StorageContext.from_defaults(vector_store=vector_store.get_vector_store())
    with timed_operation("seed_index", document_count=len(documents)):
        VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            embed_model=embed_model,
            transformations=[SentenceSplitter(chunk_size=512, chunk_overlap=64)],
        )

    log.info("seed.done", collection=settings.qdrant_collection)
    return 0


if __name__ == "__main__":
    sys.exit(main())
