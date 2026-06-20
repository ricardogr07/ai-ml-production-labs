from __future__ import annotations

import pytest

from azure_functions_text_classifier.classifier import classify_text


@pytest.mark.unit
def test_classify_incident() -> None:
    result = classify_text("Service crashed in production.")
    assert result["label"] == "incident"


@pytest.mark.unit
def test_classify_general() -> None:
    result = classify_text("Routine team update.")
    assert result["label"] == "general"


@pytest.mark.unit
def test_classify_returns_model_version() -> None:
    result = classify_text("anything")
    assert "model_version" in result
