"""Unit tests for the readiness report against a real tmp mlruns store."""

from __future__ import annotations

import pytest
from mlflow_classifier_api import readiness
from mlflow_classifier_api.errors import ModelNotReady


@pytest.mark.unit
@pytest.mark.usefixtures("ready_settings")
def test_check_model_ok_when_trained() -> None:
    readiness.check_model()  # does not raise


@pytest.mark.unit
@pytest.mark.usefixtures("unready_settings")
def test_check_model_raises_when_store_is_empty() -> None:
    with pytest.raises(ModelNotReady, match=r"run scripts/train\.py"):
        readiness.check_model()


@pytest.mark.unit
@pytest.mark.usefixtures("ready_settings")
def test_readiness_reports_ok() -> None:
    assert readiness.readiness() == {"model": "ok"}


@pytest.mark.unit
@pytest.mark.usefixtures("unready_settings")
def test_readiness_reports_failure_message_without_raising() -> None:
    report = readiness.readiness()
    assert "run scripts/train.py" in report["model"]
