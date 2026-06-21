#!/usr/bin/env python3
"""Smoke test against a running instance of the service."""

from __future__ import annotations

import argparse
import os
import sys

import httpx

DEFAULT_BASE_URL = "http://localhost:8000"


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test the FastAPI ML service.")
    parser.add_argument(
        "base_url",
        nargs="?",
        default=os.environ.get("BASE_URL", DEFAULT_BASE_URL),
        help="Base URL of the service (default: $BASE_URL or http://localhost:8000)",
    )
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")

    print(f"Target: {base_url}\n")
    client = httpx.Client(base_url=base_url, timeout=15)

    print("GET /health ...", end=" ")
    r = client.get("/health")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    assert r.json()["status"] == "ok"
    print("OK")

    print("POST /predict (incident) ...", end=" ")
    r = client.post("/predict", json={"text": "The deployment failed with an error."})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    assert r.json()["label"] == "incident"
    print("OK")

    print("POST /predict (empty text, expect 422) ...", end=" ")
    r = client.post("/predict", json={"text": ""})
    assert r.status_code == 422, f"Expected 422, got {r.status_code}"
    print("OK")

    print("\nAll smoke tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
