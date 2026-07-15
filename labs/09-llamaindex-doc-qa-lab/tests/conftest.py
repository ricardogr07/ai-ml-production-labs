"""Fixtures shared by integration and e2e tests: a real, seeded Qdrant."""

from __future__ import annotations

import pytest
from llamaindex_doc_qa_lab.config import settings
from qdrant_client import QdrantClient

_SEED_HINT = (
    "Qdrant collection not seeded, for local use: "
    "docker compose up -d && uv run python scripts/seed_data.py"
)


@pytest.fixture(scope="session")
def seeded_qdrant() -> None:
    try:
        client = QdrantClient(url=settings.qdrant_url, timeout=5)
        exists = client.collection_exists(settings.qdrant_collection)
    except Exception:
        pytest.skip("Qdrant not reachable, for local use: docker compose up -d")

    if not exists:
        pytest.skip(_SEED_HINT)
    if client.count(settings.qdrant_collection).count == 0:
        pytest.skip(_SEED_HINT)
