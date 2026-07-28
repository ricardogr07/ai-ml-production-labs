"""Readiness check for the one backing dependency: a loadable model.

`/ready` reports it without predicting; `/predict` hits the same load path and
maps failure to an actionable 503 via ModelNotReady, never a bare 500.
"""

from __future__ import annotations

from mlflow_classifier_api import service
from mlflow_classifier_api.errors import ModelNotReady


def check_model() -> None:
    """Raise ModelNotReady unless the serving model resolves and loads."""
    service.load_model()


def readiness() -> dict[str, str]:
    """Report per-dependency status: "ok" or the failure message. Never raises;
    callers decide the HTTP code from the values."""
    try:
        check_model()
        return {"model": "ok"}
    except ModelNotReady as exc:
        return {"model": str(exc)}
