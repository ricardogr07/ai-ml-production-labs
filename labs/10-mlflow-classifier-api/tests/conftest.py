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
from mlflow.tracking import MlflowClient
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


def _log_tiny_model(register: bool) -> str:
    """Log a four-label classifier into the current store; returns its run_id."""
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
            registered_model_name=settings.registered_model_name if register else None,
        )
    return run.info.run_id


@pytest.fixture(scope="session")
def trained_mlruns(tmp_path_factory: pytest.TempPathFactory) -> tuple[str, str, str]:
    """Train a tiny classifier into a fresh sqlite store, registered and aliased.

    Mirrors what scripts/train.py leaves behind, so the serving path resolves
    through the registry exactly as it does in production. Returns
    (tracking_uri, run_id, registry_version).
    """
    root = tmp_path_factory.mktemp("lab10")
    tracking_uri = _make_tracking_store(root, settings.mlflow_experiment)
    run_id = _log_tiny_model(register=True)
    client = MlflowClient()
    version = max(
        client.search_model_versions(f"name = '{settings.registered_model_name}'"),
        key=lambda candidate: int(candidate.version),
    ).version
    client.set_registered_model_alias(settings.registered_model_name, settings.model_alias, version)
    return tracking_uri, run_id, str(version)


@pytest.fixture()
def ready_settings(trained_mlruns: tuple[str, str, str], monkeypatch: pytest.MonkeyPatch) -> str:
    """Point the service at the registered store; returns the served version."""
    tracking_uri, _run_id, version = trained_mlruns
    monkeypatch.setattr(settings, "mlflow_tracking_uri", tracking_uri)
    monkeypatch.setattr(settings, "model_uri", None)
    return version


@pytest.fixture()
def unregistered_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    """A store holding a logged but unregistered model; returns its run_id.

    This is what a tracking store written before the registry existed looks
    like, and the state the latest-finished-run fallback exists to serve.
    """
    tracking_uri = _make_tracking_store(tmp_path / "unregistered", settings.mlflow_experiment)
    run_id = _log_tiny_model(register=False)
    monkeypatch.setattr(settings, "mlflow_tracking_uri", tracking_uri)
    monkeypatch.setattr(settings, "model_uri", None)
    return run_id


@pytest.fixture()
def unready_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the service at an empty tracking store: nothing was ever trained."""
    tracking_uri = _make_tracking_store(tmp_path / "empty")
    monkeypatch.setattr(settings, "mlflow_tracking_uri", tracking_uri)
    monkeypatch.setattr(settings, "model_uri", None)
