#!/usr/bin/env python3
"""
One-off script: fetch real Wikipedia article summaries for the demo corpus.

Run this by hand when the corpus needs refreshing; its output
(data/wikipedia_corpus.json) is what gets committed and read by seed_data.py.
Not part of CI or any test path, keeps seeding offline and deterministic.

Usage:
  uv run python labs/06-cosmosdb-vector-memory-lab/scripts/fetch_wikipedia_corpus.py
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

_TOPICS = [
    ("Machine learning", "ml"),
    ("Embedding (machine learning)", "ml"),
    ("Vector database", "vector"),
    ("Semantic search", "vector"),
    ("Retrieval-augmented generation", "llm"),
    ("Cosine similarity", "vector"),
    ("Nearest neighbor search", "vector"),
    ("Hierarchical navigable small world", "vector"),
    ("Large language model", "llm"),
    ("Natural language processing", "ml"),
    ("Azure Cosmos DB", "azure"),
    ("Vector space model", "vector"),
]

_API = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
_OUT = Path(__file__).parent.parent / "data" / "wikipedia_corpus.json"


def _fetch_extract(title: str) -> str:
    url = _API.format(title=urllib.parse.quote(title.replace(" ", "_")))
    if not url.startswith("https://en.wikipedia.org/"):
        raise ValueError(f"refusing to fetch non-Wikipedia URL: {url}")
    req = urllib.request.Request(
        url, headers={"User-Agent": "ai-ml-production-labs/lab-06 (contact: repo owner)"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:  # nosec B310
        data = json.load(resp)
    return data["extract"]


def main() -> int:
    docs = []
    for i, (title, source) in enumerate(_TOPICS, 1):
        extract = _fetch_extract(title)
        docs.append(
            {
                "id": f"doc-{i:02d}",
                "title": title,
                "content": extract,
                "source": source,
            }
        )
        print(f"fetched: {title} ({len(extract)} chars)")

    _OUT.parent.mkdir(parents=True, exist_ok=True)
    _OUT.write_text(json.dumps(docs, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(docs)} documents to {_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
