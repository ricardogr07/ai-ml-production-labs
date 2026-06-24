#!/usr/bin/env python3
"""Smoke test against a running instance of the Ollama Local LLM API service."""

from __future__ import annotations

import argparse
import os
import sys

import httpx

DEFAULT_BASE_URL = "http://localhost:8000"


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test the Ollama Local LLM API service.")
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
    assert r.json()["service"] == "ollama-local-llm-api"
    print("OK")

    if health_only:
        print("\nHealth-only mode: skipping /summarize tests (Ollama not available).")
        print("\nAll smoke tests passed.")
        return 0

    print("POST /summarize (tinyllama, max_tokens=64) ...", end=" ")
    r = client.post(
        "/summarize",
        json={
            "text": "Containers package an app and its dependencies into a portable unit.",
            "model": "tinyllama",
            "max_tokens": 64,
        },
        timeout=120,
    )
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    data = r.json()
    assert data["summary"], "summary must be non-empty"
    assert data["model"] == "tinyllama"
    assert data["latency_ms"] >= 0
    print("OK")

    print("POST /summarize (empty text, expect 422) ...", end=" ")
    r = client.post("/summarize", json={"text": ""})
    assert r.status_code == 422, f"Expected 422, got {r.status_code}"
    print("OK")

    print("\nAll smoke tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
