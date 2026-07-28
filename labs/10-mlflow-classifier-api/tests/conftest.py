"""Shared fixtures: a tiny model trained once into a session tmp mlruns store.

No mocks on the serving path and no network: tests exercise the real MLflow
search -> runs:/ load -> predict_proba loop against a throwaway file store.
"""

from __future__ import annotations

from collections.abc import Iterator

import mlflow
import mlflow.sklearn
import pandas as pd
import pytest
from mlflow_classifier_api import service
from mlflow_classifier_api.config import settings
from mlflow_classifier_api.service import FEATURE_COLUMNS
from sklearn.ensemble import RandomForestClassifier


@pytest.fixture(autouse=True)
def _fresh_model_cache() -> Iterator[None]:
    """Neither the process-level model cache nor MLflow's global tracking URI
    may leak between tests."""
    service.reset_model_cache()
    saved_tracking_uri = mlflow.get_tracking_uri()
    yield
    mlflow.set_tracking_uri(saved_tracking_uri)
    service.reset_model_cache()


@pytest.fixture(scope="session")
def trained_mlruns(tmp_path_factory: pytest.TempPathFactory) -> tuple[str, str]:
    """Train a tiny classifier into a fresh mlruns dir; returns (uri, run_id)."""
    # as_uri(): a raw Windows path (C:\...) parses as URI scheme "c" in MLflow.
    # The mlruns dir must not pre-exist: MLflow only bootstraps the default
    # experiment when it creates the root itself (same as train.py's ./mlruns).
    tracking_dir = (tmp_path_factory.mktemp("lab10") / "mlruns").as_uri()
    mlflow.set_tracking_uri(tracking_dir)
    frame = pd.DataFrame(
        [
            [0, 50.0, 0, 0],
            [1, 80.0, 1, 0],
            [15, 300.0, 2, 0],
            [40, 1500.0, 5, 1],
            [80, 4000.0, 15, 1],
            [90, 4500.0, 18, 1],
        ]
        * 2,
        columns=FEATURE_COLUMNS,
    )
    labels = ["low", "low", "medium", "high", "critical", "critical"] * 2
    model = RandomForestClassifier(n_estimators=2, random_state=0)
    model.fit(frame, labels)
    with mlflow.start_run() as run:
        # cloudpickle to match train.py (and because the skops default breaks
        # when other labs' tests have already imported transformers).
        mlflow.sklearn.log_model(
            model,
            "severity_classifier",
            serialization_format=mlflow.sklearn.SERIALIZATION_FORMAT_CLOUDPICKLE,
        )
    return tracking_dir, run.info.run_id


@pytest.fixture()
def ready_settings(trained_mlruns: tuple[str, str], monkeypatch: pytest.MonkeyPatch) -> str:
    """Point the service at the trained store; returns the expected run_id."""
    tracking_dir, run_id = trained_mlruns
    monkeypatch.setattr(settings, "mlflow_tracking_uri", tracking_dir)
    monkeypatch.setattr(settings, "model_uri", None)
    return run_id


@pytest.fixture()
def unready_settings(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the service at an empty tracking store: nothing was ever trained."""
    monkeypatch.setattr(settings, "mlflow_tracking_uri", (tmp_path / "empty-mlruns").as_uri())
    monkeypatch.setattr(settings, "model_uri", None)
