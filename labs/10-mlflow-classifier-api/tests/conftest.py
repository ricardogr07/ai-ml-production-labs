"""Shared fixtures: a tiny model trained once into a session tmp sqlite store.

No mocks on the serving path and no network: tests exercise the real MLflow
search -> runs:/ load -> predict_proba loop against a throwaway sqlite store.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from pathlib import Path

import mlflow
import mlflow.sklearn
import pandas as pd
import pytest
from mlflow_classifier_api import service
from mlflow_classifier_api.config import settings
from mlflow_classifier_api.service import FEATURE_COLUMNS
from sklearn.ensemble import RandomForestClassifier


def _make_tracking_store(root: Path, experiment: str | None = None) -> str:
    """Point MLflow at a fresh sqlite store under `root` and return its URI.

    A sqlite backend keeps artifacts wherever the experiment says, defaulting to
    ./mlartifacts in the process CWD, which would litter the repo during tests.
    Every experiment created here gets an explicit artifact root under `root`.
    """
    root.mkdir(parents=True, exist_ok=True)
    # as_posix(): a raw Windows path (C:\...) breaks the sqlite:/// URI.
    tracking_uri = f"sqlite:///{(root / 'mlflow.db').as_posix()}"
    mlflow.set_tracking_uri(tracking_uri)
    if experiment is not None:
        if mlflow.get_experiment_by_name(experiment) is None:
            mlflow.create_experiment(
                experiment, artifact_location=(root / "artifacts" / experiment).as_uri()
            )
        mlflow.set_experiment(experiment)
    return tracking_uri


@pytest.fixture()
def tracking_store(tmp_path: Path) -> Callable[[str], str]:
    """Factory: build a throwaway sqlite tracking store selecting `experiment`.

    Tests that log a deliberately broken artifact need their own store, separate
    from the session-scoped trained one.
    """

    def _factory(experiment: str = settings.mlflow_experiment) -> str:
        return _make_tracking_store(tmp_path / "store", experiment)

    return _factory


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
    """Train a tiny classifier into a fresh sqlite store; returns (uri, run_id)."""
    root = tmp_path_factory.mktemp("lab10")
    # Same experiment the service's latest-run lookup is scoped to.
    tracking_uri = _make_tracking_store(root, settings.mlflow_experiment)
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
    return tracking_uri, run.info.run_id


@pytest.fixture()
def ready_settings(trained_mlruns: tuple[str, str], monkeypatch: pytest.MonkeyPatch) -> str:
    """Point the service at the trained store; returns the expected run_id."""
    tracking_uri, run_id = trained_mlruns
    monkeypatch.setattr(settings, "mlflow_tracking_uri", tracking_uri)
    monkeypatch.setattr(settings, "model_uri", None)
    return run_id


@pytest.fixture()
def unready_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the service at an empty tracking store: nothing was ever trained."""
    tracking_uri = _make_tracking_store(tmp_path / "empty")
    monkeypatch.setattr(settings, "mlflow_tracking_uri", tracking_uri)
    monkeypatch.setattr(settings, "model_uri", None)
