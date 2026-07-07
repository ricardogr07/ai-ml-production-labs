"""Local, deterministic query expansion.

A small synonym dictionary scoped to the lab's corpus vocabulary, no LLM
call, keeps this lab's "no cloud dependency" scope honest, unlike an
LLM-based paraphrase/expansion approach.
"""

from __future__ import annotations

import re

_SYNONYMS: dict[str, list[str]] = {
    "ai": ["artificial intelligence", "machine learning", "neural network"],
    "deep learning": ["neural network", "machine learning"],
    "training a model": ["supervised learning", "gradient descent"],
    "bread": ["sourdough", "fermentation"],
    "chef technique": ["sous vide", "umami"],
    "flavor": ["umami", "fermentation"],
    "ancient civilization": ["roman empire"],
    "revolution": ["french revolution", "industrial revolution"],
    "soccer": ["association football"],
    "space": ["black hole", "exoplanet", "milky way", "supernova", "neutron star"],
    "star": ["supernova", "neutron star"],
    "running race": ["marathon"],
}


def expand_query(query: str) -> str:
    lowered = query.lower()
    extra: list[str] = []
    for term, synonyms in _SYNONYMS.items():
        if re.search(rf"\b{re.escape(term)}\b", lowered):
            extra.extend(s for s in synonyms if s not in extra)
    if not extra:
        return query
    return f"{query} {' '.join(extra)}"
