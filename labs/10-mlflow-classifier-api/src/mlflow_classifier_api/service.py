"""Model resolution and inference.

Loads the classifier lazily on first use (never at import, so an empty
tracking store cannot crash app startup), caches it for the process, and maps
IncidentFeatures to a SeverityResponse via predict_proba.
"""

from __future__ import annotations

import logging
import os
import threading
from typing import Any, cast

import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd

from mlflow_classifier_api.config import settings
from mlflow_classifier_api.errors import ModelNotReady
from mlflow_classifier_api.schemas import IncidentFeatures, SeverityResponse

# Must match the training frame column order in scripts/train.py
# (df.drop("severity") keeps: error_count, latency_p95_ms, failed_jobs,
# deployment_recent). _resolve_and_load verifies this against the artifact.
FEATURE_COLUMNS = ["error_count", "latency_p95_ms", "failed_jobs", "deployment_recent"]

# Keep in sync with the SeverityResponse.severity Literal in schemas.py and
# LABELS in scripts/train.py. A model may know a subset (small training data),
# never a label outside this set.
_VALID_LABELS = {"low", "medium", "high", "critical"}

_ARTIFACT_NAME = "severity_classifier"

# ponytail: MLflow 3.14 hard-errors on the ./mlruns file store (maintenance
# mode) unless this is set; the lab is local-first so we allow it. Ceiling is
# MLflow dropping the file store entirely; upgrade path is a sqlite backend
# (W2). setdefault, so an operator's explicit value wins. The store is built
# lazily on first client call, so setting this at import time is early enough.
os.environ.setdefault("MLFLOW_ALLOW_FILE_STORE", "true")

_MODEL_CACHE: tuple[Any, str] | None = None
_LOAD_LOCK = threading.Lock()

logger = logging.getLogger(__name__)


def load_model() -> tuple[Any, str]:
    """Return the cached (model, version), loading it single-flight on first use.

    Double-checked locking: concurrent first requests trigger one load, not a
    thundering herd against the artifact store. Failures are never cached, so
    the next request retries (e.g. after scripts/train.py finally runs).
    """
    global _MODEL_CACHE
    if _MODEL_CACHE is None:
        with _LOAD_LOCK:
            if _MODEL_CACHE is None:
                _MODEL_CACHE = _resolve_and_load()
    return _MODEL_CACHE


def reset_model_cache() -> None:
    """Forget the cached model (tests; or a manual reload after retraining)."""
    global _MODEL_CACHE
    with _LOAD_LOCK:
        _MODEL_CACHE = None


def _resolve_and_load() -> tuple[Any, str]:
    """Resolve the serving model URI, load it, and sanity-check the artifact."""
    # ponytail: serves the latest finished run, no version pinning; the ceiling
    # is reproducibility across retrains. Pin via MODEL_URI when it matters;
    # registry-backed pinning is the W2 upgrade path.
    try:
        mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
        if settings.model_uri:
            uri = version = settings.model_uri
        else:
            # Experiment name, never the tracking URI: ModelNotReady messages
            # go to unauthenticated callers and the URI may carry credentials.
            no_runs = (
                f"No finished runs in MLflow experiment {settings.mlflow_experiment!r}; "
                "run scripts/train.py first."
            )
            experiment = mlflow.get_experiment_by_name(settings.mlflow_experiment)
            if experiment is None:
                raise ModelNotReady(no_runs)
            # cast: mlflow's stubs mistype the "list" output's Run entities
            runs = cast(
                "list[Any]",
                mlflow.search_runs(
                    experiment_ids=[experiment.experiment_id],
                    filter_string="attributes.status = 'FINISHED'",
                    order_by=["attributes.start_time DESC"],
                    max_results=1,
                    output_format="list",
                ),
            )
            if not runs:
                raise ModelNotReady(no_runs)
            version = runs[0].info.run_id
            uri = f"runs:/{version}/{_ARTIFACT_NAME}"
        model = mlflow.sklearn.load_model(uri)
    except ModelNotReady:
        raise
    except Exception as exc:  # any MLflow/store fault means not ready, never a 500
        # Full cause (which may embed the credentialed tracking URI) stays in
        # server logs; the client-facing message never carries either.
        logger.exception("Model load failed")
        raise ModelNotReady(
            "Failed to load the serving model from the tracking store; "
            "see server logs for the cause."
        ) from exc

    trained_columns = getattr(model, "feature_names_in_", None)
    if trained_columns is not None and list(trained_columns) != FEATURE_COLUMNS:
        raise ModelNotReady(
            f"Model was trained on features {list(trained_columns)} but the API serves "
            f"{FEATURE_COLUMNS}; retrain with scripts/train.py."
        )
    unknown_labels = {str(label) for label in getattr(model, "classes_", [])} - _VALID_LABELS
    if unknown_labels:
        raise ModelNotReady(
            f"Model predicts labels {sorted(unknown_labels)} outside the API contract "
            f"{sorted(_VALID_LABELS)}; retrain with scripts/train.py."
        )
    if not callable(getattr(model, "predict_proba", None)):
        raise ModelNotReady(
            "Model artifact does not implement predict_proba, which /predict "
            "requires; retrain with scripts/train.py."
        )
    return model, version


def predict(features: IncidentFeatures) -> SeverityResponse:
    model, version = load_model()
    frame = pd.DataFrame(
        [
            [
                features.error_count,
                features.latency_p95_ms,
                features.failed_jobs,
                int(features.deployment_recent),
            ]
        ],
        columns=FEATURE_COLUMNS,
    )
    proba = model.predict_proba(frame)[0]
    best = int(np.argmax(proba))
    return SeverityResponse(
        severity=model.classes_[best],
        confidence=float(proba[best]),
        model_version=version,
    )
