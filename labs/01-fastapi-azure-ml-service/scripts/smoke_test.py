#!/usr/bin/env python3
"""Smoke test against a running instance of the service."""

from __future__ import annotations

import sys

import httpx

BASE_URL = "http://localhost:8000"


def main() -> int:
    client = httpx.Client(base_url=BASE_URL, timeout=10)

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
