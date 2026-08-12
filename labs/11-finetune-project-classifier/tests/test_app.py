import pytest
from fastapi.testclient import TestClient
from finetune_project_classifier.app import app


@pytest.mark.integration
def test_health() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "finetune-project-classifier"


@pytest.mark.integration
def test_predict_is_unavailable_before_training() -> None:
    response = TestClient(app).post("/predict", json={"description": "A vector search API"})
    assert response.status_code in {200, 503}


@pytest.mark.unit
def test_predict_rejects_empty_description() -> None:
    response = TestClient(app).post("/predict", json={"description": ""})
    assert response.status_code == 422
