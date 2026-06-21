"""Deterministic text classifier for the Azure Functions lab."""

from __future__ import annotations


def classify_text(text: str) -> dict[str, object]:
    """Return a classification result for the given text."""
    lower = text.lower()
    if any(kw in lower for kw in ("error", "failed", "crash", "outage")):
        label, confidence = "incident", 0.85
    elif any(kw in lower for kw in ("feature", "release", "deploy")):
        label, confidence = "deployment", 0.75
    else:
        label, confidence = "general", 0.60

    return {"label": label, "confidence": confidence, "model_version": "rules-v0.1.0"}
