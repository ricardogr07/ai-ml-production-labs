"""End-to-end smoke test for finetune → serve → predict pipeline.

Validates that:
1. Model artifacts exist and are valid
2. Metrics show training improvement
3. Service loads model without errors
4. Readiness check passes
5. HTTP endpoints work (/health, /ready, /predict)
6. Predictions return valid schema and confidence
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient
from finetune_project_classifier.app import app
from finetune_project_classifier.config import settings
from finetune_project_classifier.dataset import LABELS, SAMPLES
from finetune_project_classifier.errors import ModelNotReadyError
from finetune_project_classifier.readiness import readiness
from finetune_project_classifier.service import load_model, reset_model_cache


@pytest.mark.integration
def test_finetune_to_predict_smoke() -> None:
    """Full smoke test: train → validate artifacts → load model → serve predictions.

    Assertion sequence:
    1. Model artifacts exist (config.json, pytorch_model.bin, tokenizer.json)
    2. metrics.json parses and has required fields
    3. fine_tuned_accuracy ≥ baseline_accuracy (training improved)
    4. load_model() succeeds and returns valid tuple
    5. readiness() returns {"model": "ok"}
    6. /health endpoint returns 200
    7. /ready endpoint returns 200 with ready=true
    8. /predict with sample input returns 200 and valid schema
    9. Prediction response has valid label, confidence [0-1], model_version="local"
    """

    model_dir = settings.model_dir

    # Assertion 1: Artifacts exist and have expected files
    assert model_dir.exists(), (
        f"Model directory not found at {model_dir}; run scripts/finetune.py first."
    )
    assert (model_dir / "config.json").exists(), "config.json missing"
    # Model saved as safetensors or pytorch_model.bin (both valid)
    has_model = (model_dir / "model.safetensors").exists() or (
        model_dir / "pytorch_model.bin"
    ).exists()
    assert has_model, "model.safetensors or pytorch_model.bin missing"
    assert (model_dir / "tokenizer.json").exists(), "tokenizer.json missing"

    # Assertion 2: metrics.json parses and has required fields
    metrics_path = model_dir / "metrics.json"
    assert metrics_path.exists(), "metrics.json missing"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert "baseline_accuracy" in metrics, "baseline_accuracy not in metrics"
    assert "fine_tuned_accuracy" in metrics, "fine_tuned_accuracy not in metrics"
    assert "samples" in metrics, "samples count not in metrics"

    # Assertion 3: Training improved baseline
    baseline = metrics["baseline_accuracy"]
    fine_tuned = metrics["fine_tuned_accuracy"]
    assert fine_tuned >= baseline, (
        f"Fine-tuned accuracy ({fine_tuned}) did not improve baseline ({baseline})"
    )
    assert metrics["samples"] == 18, f"Expected 18 samples, got {metrics['samples']}"

    # Reset service cache before loading model
    reset_model_cache()

    # Assertion 4: load_model() succeeds and returns valid tuple
    try:
        tokenizer, model, version = load_model()
    except ModelNotReadyError as exc:
        pytest.fail(f"load_model() failed: {exc}")
    assert tokenizer is not None, "tokenizer is None"
    assert model is not None, "model is None"
    assert version == "local", f"Expected version='local', got '{version}'"

    # Assertion 5: readiness() returns {"model": "ok"}
    ready_status = readiness()
    assert ready_status == {"model": "ok"}, (
        f"readiness() returned {ready_status}, expected {{'model': 'ok'}}"
    )

    # Create FastAPI test client
    client = TestClient(app)

    # Assertion 6: /health endpoint returns 200
    health_response = client.get("/health")
    assert health_response.status_code == 200, (
        f"GET /health returned {health_response.status_code}, expected 200"
    )
    health_data = health_response.json()
    assert health_data.get("service") == "finetune-project-classifier", (
        f"health service name mismatch: {health_data.get('service')}"
    )

    # Assertion 7: /ready endpoint returns 200 with ready=true
    ready_response = client.get("/ready")
    assert ready_response.status_code == 200, (
        f"GET /ready returned {ready_response.status_code}, expected 200"
    )
    ready_data = ready_response.json()
    assert ready_data.get("ready") is True, (
        f"/ready ready field is {ready_data.get('ready')}, expected True"
    )

    # Assertion 8: /predict with sample input returns 200 and valid schema
    sample_description = SAMPLES[0][0]  # "FastAPI service deployed to Azure..."
    predict_payload = {"description": sample_description}
    predict_response = client.post("/predict", json=predict_payload)
    assert predict_response.status_code == 200, (
        f"POST /predict returned {predict_response.status_code}, expected 200"
    )

    # Assertion 9: Prediction response has valid label, confidence, model_version
    pred_data = predict_response.json()
    assert "label" in pred_data, "label field missing in response"
    assert "confidence" in pred_data, "confidence field missing in response"
    assert "model_version" in pred_data, "model_version field missing in response"

    label = pred_data["label"]
    assert label in LABELS, f"Predicted label '{label}' not in valid labels {LABELS}"

    confidence = pred_data["confidence"]
    assert isinstance(confidence, float), f"confidence should be float, got {type(confidence)}"
    assert 0.0 <= confidence <= 1.0, f"confidence {confidence} out of valid range [0.0, 1.0]"

    model_version = pred_data["model_version"]
    assert model_version == "local", f"model_version expected 'local', got '{model_version}'"

    # Clean up: reset cache for subsequent tests
    reset_model_cache()
