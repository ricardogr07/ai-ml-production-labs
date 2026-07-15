#!/usr/bin/env python3
"""Smoke test against a running instance of the LlamaIndex Doc QA service.

Assumes the Qdrant collection has already been seeded (scripts/seed_data.py).
"""

from __future__ import annotations

import argparse
import os
import sys

import httpx

DEFAULT_BASE_URL = "http://localhost:8000"


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test the LlamaIndex Doc QA service.")
    parser.add_argument(
        "base_url",
        nargs="?",
        default=os.environ.get("BASE_URL", DEFAULT_BASE_URL),
        help="Base URL of the service (default: $BASE_URL or http://localhost:8000)",
    )
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")
    health_only = os.environ.get("HEALTH_ONLY", "").lower() in ("1", "true", "yes")

    print(f"Target: {base_url}")
    print(f"Mode: {'health-only' if health_only else 'full'}\n")
    client = httpx.Client(base_url=base_url, timeout=15)

    print("GET /health ...", end=" ")
    r = client.get("/health")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    assert r.json()["status"] == "ok"
    assert r.json()["service"] == "llamaindex-doc-qa-lab"
    print("OK")

    if health_only:
        print("\nHealth-only mode: skipping /ready and /query (backing services unavailable).")
        print("\nAll smoke tests passed.")
        return 0

    print("GET /ready ...", end=" ")
    r = client.get("/ready")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    assert r.json()["ready"] is True, f"Service not ready: {r.text}"
    print("OK")

    print("POST /query (top_k=2) ...", end=" ")
    r = client.post(
        "/query",
        json={"question": "What is DNA?", "top_k": 2},
        timeout=120,
    )
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    data = r.json()
    assert data["answer"], "answer must be non-empty"
    n_sources = len(data["sources"])
    assert 1 <= n_sources <= 2, f"Expected 1 to 2 cited sources, got {n_sources}"
    print("OK")

    print("POST /query (empty question, expect 422) ...", end=" ")
    r = client.post("/query", json={"question": ""})
    assert r.status_code == 422, f"Expected 422, got {r.status_code}"
    print("OK")

    print("\nAll smoke tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
