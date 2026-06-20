# Lab 10: MLflow Classifier API

## What this proves

Classical ML engineering end-to-end: synthetic dataset generation, model training with MLflow experiment tracking, model artifact persistence, and inference via FastAPI. The domain is software incident severity classification.

## Scope

- Capability: Train a Random Forest severity classifier and serve it via FastAPI
- Input: `{ service_name, error_count, latency_p95_ms, failed_jobs, deployment_recent }`
- Output: `{ severity: low|medium|high|critical, confidence, model_version }`
- Deployment target: Azure Container Apps (containerized FastAPI)
- Non-goals: real incident data, online learning, multi-model serving

## Architecture

```text
train.py → synthetic dataset → RandomForestClassifier → MLflow artifact
                                                              ↓
                                    FastAPI /predict → model.predict() → SeverityResponse
```

## Run locally

```bash
uv sync

# Train and log to MLflow
uv run --package mlflow-classifier-api python labs/10-mlflow-classifier-api/scripts/train.py

# Inspect runs
uv run mlflow ui

# Start API (after training)
uv run --package mlflow-classifier-api uvicorn mlflow_classifier_api.app:app --reload
```

## Test

```bash
uv run --package mlflow-classifier-api pytest labs/10-mlflow-classifier-api/tests
```

## Tradeoffs

- Synthetic dataset: real incident data would be confidential. The synthetic generator preserves the feature engineering pattern.
- No model registry in the scaffold; `mlflow.sklearn.log_model` is enough to demonstrate the tracking pattern.
- Model is loaded at startup from the latest MLflow run; production would pin a specific run ID.
