"""Domain errors mapped to actionable HTTP responses in app.py.

Keeps provider/store exception knowledge out of the FastAPI layer: the service
raises these, app.py maps NotReadyError -> 503 and GenerationError -> 424.
"""

from __future__ import annotations


class NotReadyError(Exception):
    """A backing dependency is not ready to serve a query (unseeded Qdrant, a
    stale vector schema, an unreachable Ollama, a missing model, or a missing
    Anthropic key). The message is safe to return to the caller."""


class GenerationError(Exception):
    """Retrieval or generation failed at query time after readiness passed
    (provider error, timeout, or a bad credential surfacing only on the call)."""
