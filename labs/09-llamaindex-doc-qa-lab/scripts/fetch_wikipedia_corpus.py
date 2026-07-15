#!/usr/bin/env python3
"""
One-off script: fetch real Wikipedia article summaries for the RAG corpus.

Run this by hand when the corpus needs refreshing; its output
(data/wikipedia_corpus.json) is what gets committed and read by
scripts/seed_data.py. Not part of CI or any test path, keeps seeding
offline and deterministic.

Usage:
  uv run python labs/09-llamaindex-doc-qa-lab/scripts/fetch_wikipedia_corpus.py
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

_TOPICS = [
    ("Mount Everest", "geography"),
    ("Amazon rainforest", "geography"),
    ("Sahara", "geography"),
    ("Great Barrier Reef", "geography"),
    ("Nile", "geography"),
    ("Internet", "technology"),
    ("Semiconductor", "technology"),
    ("Robotics", "technology"),
    ("Blockchain", "technology"),
    ("Quantum computing", "technology"),
    ("DNA", "biology"),
    ("Photosynthesis", "biology"),
    ("Immune system", "biology"),
    ("Evolution", "biology"),
    ("Cell (biology)", "biology"),
    ("Stoicism", "philosophy"),
    ("Existentialism", "philosophy"),
    ("Utilitarianism", "philosophy"),
    ("Socratic method", "philosophy"),
    ("Epistemology", "philosophy"),
]

_API = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
_OUT = Path(__file__).parent.parent / "data" / "wikipedia_corpus.json"


def _fetch_extract(title: str) -> str:
    url = _API.format(title=urllib.parse.quote(title.replace(" ", "_")))
    if not url.startswith("https://en.wikipedia.org/"):
        raise ValueError(f"refusing to fetch non-Wikipedia URL: {url}")
    req = urllib.request.Request(
        url, headers={"User-Agent": "ai-ml-production-labs/lab-09 (contact: repo owner)"}
    )
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:  # nosec B310
                data = json.load(resp)
            return data["extract"]
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt == 4:
                raise
            wait = 30 * (attempt + 1)
            print(f"  rate limited, waiting {wait}s...")
            time.sleep(wait)
    raise RuntimeError("unreachable")


def main() -> int:
    docs = []
    for i, (title, category) in enumerate(_TOPICS, 1):
        if i > 1:
            time.sleep(1)
        extract = _fetch_extract(title)
        docs.append(
            {
                "id": f"doc-{i:02d}",
                "title": title,
                "content": extract,
                "category": category,
            }
        )
        print(f"fetched: {title} ({category}, {len(extract)} chars)")

    _OUT.parent.mkdir(parents=True, exist_ok=True)
    _OUT.write_text(json.dumps(docs, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(docs)} documents to {_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
