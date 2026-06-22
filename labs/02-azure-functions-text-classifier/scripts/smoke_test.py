#!/usr/bin/env python3
"""Smoke test against a running instance of the text classifier function."""

from __future__ import annotations

import argparse
import os
import sys

import httpx

DEFAULT_BASE_URL = "http://localhost:7071"


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test the Azure Functions text classifier.")
    parser.add_argument(
        "base_url",
        nargs="?",
        default=os.environ.get("BASE_URL", DEFAULT_BASE_URL),
        help="Base URL of the function app (default: $BASE_URL or http://localhost:7071)",
    )
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")

    print(f"Target: {base_url}\n")
    client = httpx.Client(base_url=base_url, timeout=30)

    print("POST /api/classify (incident) ...", end=" ")
    r = client.post("/api/classify", json={"text": "Service crashed in production."})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    body = r.json()
    assert body["label"] == "incident", f"Expected 'incident', got {body['label']!r}"
    assert 0.0 <= body["confidence"] <= 1.0
    assert body["model_version"]
    print("OK")

    print("POST /api/classify (deployment) ...", end=" ")
    r = client.post("/api/classify", json={"text": "New release deployed to staging."})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    assert r.json()["label"] == "deployment"
    print("OK")

    print("POST /api/classify (general) ...", end=" ")
    r = client.post("/api/classify", json={"text": "Routine team update."})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    assert r.json()["label"] == "general"
    print("OK")

    print("POST /api/classify (empty text, expect 422) ...", end=" ")
    r = client.post("/api/classify", json={"text": ""})
    assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text}"
    assert "detail" in r.json()
    print("OK")

    print("POST /api/classify (invalid JSON, expect 400) ...", end=" ")
    r = client.post(
        "/api/classify",
        content=b"not valid json{{{",
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 400, f"Expected 400, got {r.status_code}: {r.text}"
    assert "detail" in r.json()
    print("OK")

    print("\nAll smoke tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
