"""Domain errors mapped to actionable HTTP responses in app.py.

Keeps MLflow exception knowledge out of the FastAPI layer: the service raises
ModelNotReady, app.py maps it to 503.
"""

from __future__ import annotations


class ModelNotReady(Exception):  # noqa: N818 (name is the lab's public contract)
    """No serving model is available (empty tracking store, unloadable artifact,
    or a train/serve feature mismatch). The message is safe to return to the
    caller and says how to fix it."""
