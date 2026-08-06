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
train.py → synthetic dataset → RandomForestClassifier → registered version → champion alias
                                                                                   ↓
                                    FastAPI /predict → model.predict_proba() → SeverityResponse
```

## Run locally

```bash
uv sync

# Train and log to MLflow (metadata in ./mlflow.db, artifacts under ./mlruns)
uv run --package mlflow-classifier-api python labs/10-mlflow-classifier-api/scripts/train.py

# Inspect runs
uv run mlflow ui --backend-store-uri sqlite:///mlflow.db

# Start API (after training)
uv run --package mlflow-classifier-api uvicorn mlflow_classifier_api.app:app --reload
```

## Docker

The image trains at build time, so it serves a model on first request with no
setup. Run from the repo root (the build context is the whole workspace):

```bash
docker build -f labs/10-mlflow-classifier-api/Dockerfile -t mlflow-classifier-api .
docker run --rm -p 8000:8000 mlflow-classifier-api
```

`/health` and `/ready` both return 200; `POST /predict` serves the baked model.
Point `MLFLOW_TRACKING_URI` at a store with no finished run to get the
untrained behavior back (`/ready` and `/predict` return 503):

```bash
docker run --rm -p 8000:8000 -e MLFLOW_TRACKING_URI=sqlite:////tmp/empty.db mlflow-classifier-api
```

## Compose

The compose stack takes the mounted-store path instead: a named volume holds
the tracking DB and the artifact tree, and training is a one-off service.

```bash
cd labs/10-mlflow-classifier-api

docker compose up -d --build   # /health 200, /ready 503 (no runs yet)
docker compose run --rm train  # /ready 200 on the next request, no restart
docker compose down -v
```

## Verify a running instance

`smoke_test.py` checks a deployed or containerized instance end to end:
`/health`, `/ready`, a valid `/predict`, and a rejected one.

```bash
uv run --package mlflow-classifier-api \
  python labs/10-mlflow-classifier-api/scripts/smoke_test.py http://localhost:8000
```

It exits non-zero on the first failed assertion. Set `HEALTH_ONLY=1` to check
only `/health` when the instance has no trained model yet.

## Test

```bash
uv run --package mlflow-classifier-api pytest labs/10-mlflow-classifier-api/tests
```

## Tradeoffs

- Synthetic dataset: real incident data would be confidential. The synthetic generator preserves the feature engineering pattern.
- Training promotes unconditionally: every run moves the `champion` alias to the version it just registered. A real pipeline would gate promotion on the eval metric beating the incumbent, which this lab cannot demonstrate on a fixed seed.
- Model is loaded lazily on first use and cached for the process, so an empty tracking store returns an actionable 503 instead of crashing startup. Resolution order is `MODEL_URI`, then the registry alias, then the latest finished run; the last is a fallback for stores written before the registry existed.
- The image bakes a trained model rather than mounting a store. Azure Container Apps has no persistent volume by default, so a non-baked image would serve 503 until someone shelled in and trained. Baking is honest here only because the training data is synthetic and seeded; with real data the artifact would have to come from a mounted store or a tracking server.
