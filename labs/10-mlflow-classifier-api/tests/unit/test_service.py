"""Unit tests for model resolution and inference against a real tmp sqlite store."""

from __future__ import annotations

from collections.abc import Callable

import mlflow
import mlflow.sklearn
import pandas as pd
import pytest
from mlflow_classifier_api import service
from mlflow_classifier_api.config import settings
from mlflow_classifier_api.errors import ModelNotReady
from mlflow_classifier_api.schemas import IncidentFeatures
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import LinearSVC

_CRITICAL_INCIDENT = IncidentFeatures(
    service_name="auth-service",
    error_count=90,
    latency_p95_ms=4200.0,
    failed_jobs=17,
    deployment_recent=True,
)


@pytest.mark.unit
def test_load_model_resolves_registry_alias(ready_settings: str) -> None:
    """The default serving path is the alias, and the reported version is the
    registry version number, not a run id."""
    model, version = service.load_model()
    assert version == ready_settings
    assert version.isdigit()
    assert list(model.feature_names_in_) == service.FEATURE_COLUMNS


@pytest.mark.unit
def test_load_model_falls_back_to_latest_run_when_alias_missing(
    unregistered_settings: str,
) -> None:
    """A store written before the registry existed still serves: no alias, so
    resolution falls back to the newest finished run."""
    _model, version = service.load_model()
    assert version == unregistered_settings


@pytest.mark.unit
def test_load_model_missing_alias_and_no_runs_raises_model_not_ready(
    tracking_store: Callable[[], str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Neither an alias nor a finished run: the 503 must name train.py and must
    not leak the tracking URI."""
    tracking_uri = tracking_store()
    monkeypatch.setattr(settings, "mlflow_tracking_uri", tracking_uri)
    monkeypatch.setattr(settings, "model_uri", None)

    with pytest.raises(ModelNotReady, match=r"run scripts/train\.py") as excinfo:
        service.load_model()
    assert tracking_uri not in str(excinfo.value)


@pytest.mark.unit
@pytest.mark.usefixtures("unready_settings")
def test_load_model_empty_store_raises_model_not_ready() -> None:
    with pytest.raises(ModelNotReady, match=r"run scripts/train\.py"):
        service.load_model()


@pytest.mark.unit
def test_load_model_rejects_feature_mismatch(
    tracking_store: Callable[[], str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A model trained on different columns must fail loading with an
    actionable message, not silently mis-predict on reordered features."""
    tracking_uri = tracking_store()
    wrong = pd.DataFrame([[1, 2], [3, 4]], columns=["a", "b"])
    model = RandomForestClassifier(n_estimators=1, random_state=0)
    model.fit(wrong, ["low", "high"])
    with mlflow.start_run():
        mlflow.sklearn.log_model(
            model,
            "severity_classifier",
            serialization_format=mlflow.sklearn.SERIALIZATION_FORMAT_CLOUDPICKLE,
        )
    monkeypatch.setattr(settings, "mlflow_tracking_uri", tracking_uri)
    monkeypatch.setattr(settings, "model_uri", None)

    with pytest.raises(ModelNotReady, match="retrain"):
        service.load_model()


@pytest.mark.unit
def test_load_model_rejects_labels_outside_contract(
    tracking_store: Callable[[], str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """An artifact predicting labels the API contract does not know must be
    rejected at load with an actionable message, not 500 at predict time."""
    tracking_uri = tracking_store()
    frame = pd.DataFrame([[1, 2.0, 3, 0], [4, 5.0, 6, 1]], columns=service.FEATURE_COLUMNS)
    model = RandomForestClassifier(n_estimators=1, random_state=0)
    model.fit(frame, ["low", "catastrophic"])
    with mlflow.start_run():
        mlflow.sklearn.log_model(
            model,
            "severity_classifier",
            serialization_format=mlflow.sklearn.SERIALIZATION_FORMAT_CLOUDPICKLE,
        )
    monkeypatch.setattr(settings, "mlflow_tracking_uri", tracking_uri)
    monkeypatch.setattr(settings, "model_uri", None)

    with pytest.raises(ModelNotReady, match="catastrophic"):
        service.load_model()


@pytest.mark.unit
def test_load_model_failure_hides_tracking_uri(
    trained_mlruns: tuple[str, str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Load failures must not echo the tracking URI (it may carry credentials)
    or the raw MLflow error into the client-facing 503 message."""
    tracking_uri, _run_id, _version = trained_mlruns
    monkeypatch.setattr(settings, "mlflow_tracking_uri", tracking_uri)
    monkeypatch.setattr(settings, "model_uri", "runs:/no-such-run/severity_classifier")

    with pytest.raises(ModelNotReady) as excinfo:
        service.load_model()
    assert tracking_uri not in str(excinfo.value)
    assert "server logs" in str(excinfo.value)


@pytest.mark.unit
def test_fallback_ignores_newer_run_in_other_experiment(
    unregistered_settings: str,
) -> None:
    """A newer finished run in an unrelated experiment must not shadow the
    classifier: the fallback lookup is scoped to the configured experiment."""
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    mlflow.set_experiment("unrelated-experiment")
    with mlflow.start_run():
        pass  # finished run, newer than the classifier's, no artifact

    _model, version = service.load_model()
    assert version == unregistered_settings


@pytest.mark.unit
def test_load_model_rejects_model_without_predict_proba(
    tracking_store: Callable[[], str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A classifier without predict_proba must fail readiness at load, not 500
    on the first /predict."""
    tracking_uri = tracking_store()
    frame = pd.DataFrame([[1, 2.0, 3, 0], [4, 5.0, 6, 1]], columns=service.FEATURE_COLUMNS)
    model = LinearSVC()
    model.fit(frame, ["low", "high"])
    with mlflow.start_run():
        mlflow.sklearn.log_model(
            model,
            "severity_classifier",
            serialization_format=mlflow.sklearn.SERIALIZATION_FORMAT_CLOUDPICKLE,
        )
    monkeypatch.setattr(settings, "mlflow_tracking_uri", tracking_uri)
    monkeypatch.setattr(settings, "model_uri", None)

    with pytest.raises(ModelNotReady, match="predict_proba"):
        service.load_model()


@pytest.mark.unit
def test_load_model_honors_model_uri_override(
    trained_mlruns: tuple[str, str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """MODEL_URI wins over the alias: the explicit pin is the escape hatch."""
    tracking_uri, run_id, _version = trained_mlruns
    pinned = f"runs:/{run_id}/severity_classifier"
    monkeypatch.setattr(settings, "mlflow_tracking_uri", tracking_uri)
    monkeypatch.setattr(settings, "model_uri", pinned)
    _model, version = service.load_model()
    assert version == pinned


@pytest.mark.unit
def test_predict_returns_valid_severity_response(ready_settings: str) -> None:
    response = service.predict(_CRITICAL_INCIDENT)
    assert response.severity == "critical"
    assert 0.0 <= response.confidence <= 1.0
    assert response.model_version == ready_settings


@pytest.mark.unit
@pytest.mark.usefixtures("ready_settings")
def test_predict_confidence_is_max_class_probability() -> None:
    model, _version = service.load_model()
    response = service.predict(_CRITICAL_INCIDENT)
    frame = pd.DataFrame(
        [[90, 4200.0, 17, 1]],
        columns=service.FEATURE_COLUMNS,
    )
    assert response.confidence == pytest.approx(model.predict_proba(frame)[0].max())


@pytest.mark.unit
@pytest.mark.usefixtures("unready_settings")
def test_predict_without_model_raises_model_not_ready() -> None:
    with pytest.raises(ModelNotReady):
        service.predict(_CRITICAL_INCIDENT)
