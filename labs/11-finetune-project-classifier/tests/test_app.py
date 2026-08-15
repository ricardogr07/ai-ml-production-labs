from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from finetune_project_classifier import service
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
def test_predict_returns_service_unavailable_for_incomplete_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "config.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(service.settings, "model_dir", tmp_path)
    service.reset_model_cache()

    response = TestClient(app).post("/predict", json={"description": "A vector search API"})

    assert response.status_code == 503
    assert "incomplete or invalid" in response.json()["detail"]
    service.reset_model_cache()


@pytest.mark.unit
def test_predict_rejects_empty_description() -> None:
    response = TestClient(app).post("/predict", json={"description": ""})
    assert response.status_code == 422
