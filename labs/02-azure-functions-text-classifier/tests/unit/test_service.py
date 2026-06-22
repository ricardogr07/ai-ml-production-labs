from __future__ import annotations

import pytest
from azure_functions_text_classifier.schemas import ClassifyRequest
from azure_functions_text_classifier.service import ClassifierService


@pytest.fixture
def service() -> ClassifierService:
    return ClassifierService()


@pytest.mark.unit
def test_classify_incident(service: ClassifierService) -> None:
    result = service.classify(ClassifyRequest(text="Service crashed in production."))
    assert result.label == "incident"
    assert 0.0 <= result.confidence <= 1.0


@pytest.mark.unit
def test_classify_deployment(service: ClassifierService) -> None:
    result = service.classify(ClassifyRequest(text="New release deployed to staging."))
    assert result.label == "deployment"
    assert 0.0 <= result.confidence <= 1.0


@pytest.mark.unit
def test_classify_general(service: ClassifierService) -> None:
    result = service.classify(ClassifyRequest(text="Routine team update."))
    assert result.label == "general"
    assert 0.0 <= result.confidence <= 1.0


@pytest.mark.unit
def test_classify_returns_model_version(service: ClassifierService) -> None:
    result = service.classify(ClassifyRequest(text="anything"))
    assert result.model_version != ""


@pytest.mark.unit
def test_classify_confidence_in_range(service: ClassifierService) -> None:
    for text in ("system outage detected", "deploy complete", "weekly sync notes"):
        result = service.classify(ClassifyRequest(text=text))
        assert 0.0 <= result.confidence <= 1.0
