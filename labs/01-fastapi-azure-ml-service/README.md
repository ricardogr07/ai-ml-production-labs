# Lab 01: FastAPI Azure ML Service

## What this proves

A production-shaped containerized FastAPI service deployed to Azure Container Apps. The service exposes a `/predict` endpoint with typed request/response schemas, input validation, structured logging, a health check, and a Dockerfile that builds cleanly from the monorepo root.

## Scope

- Capability: HTTP prediction API with deterministic rule-based scoring
- Input: `{ "text": "..." }` (1–10,000 characters)
- Output: `{ "label": "...", "confidence": 0.0–1.0, "model_version": "..." }`
- Deployment target: Azure Container Apps
- Non-goals: real ML model training, authentication, streaming responses

## Architecture

```text
client
  → POST /predict → PredictionService → rule-based scorer → PredictResponse
  → GET  /health  → HealthResponse
```

## Tech stack

- Python 3.12
- FastAPI + Uvicorn
- Pydantic v2
- structlog
- uv workspace
- tox + tox-uv
- pytest
- ruff
- pyrefly
- Docker
- Azure Container Apps (Terraform)

## Run locally

```bash
uv sync
uv run --package fastapi-azure-ml-service uvicorn fastapi_azure_ml_service.app:app --reload
```

## Test

```bash
uv run --package fastapi-azure-ml-service pytest labs/01-fastapi-azure-ml-service/tests
# or from repo root:
uv run tox -e lint,type,py312,security,audit
```

## Docker

```bash
# Build from repo root
docker build -f labs/01-fastapi-azure-ml-service/Dockerfile -t fastapi-azure-ml-service:local .

# Run
docker run --rm -p 8000:8000 --env-file labs/01-fastapi-azure-ml-service/.env.example fastapi-azure-ml-service:local

# Or with docker-compose (from lab directory)
docker compose up
```

## Smoke test

```bash
python scripts/smoke_test.py
```

## API examples

**Health check**

```
GET /health

200 OK
{
  "status": "ok",
  "service": "fastapi-azure-ml-service",
  "version": "0.1.0",
  "timestamp_utc": "2026-06-20T10:00:00Z"
}
```

**Predict: incident**

```
POST /predict
{ "text": "The deployment failed with an error." }

200 OK
{
  "label": "incident",
  "confidence": 0.85,
  "model_version": "rules-v0.1.0"
}
```

**Predict: general**

```
POST /predict
{ "text": "Routine status update from the team." }

200 OK
{
  "label": "general",
  "confidence": 0.65,
  "model_version": "rules-v0.1.0"
}
```

**Validation failure**

```
POST /predict
{ "text": "" }

422 Unprocessable Entity
```

## Production notes

- Replace the rule-based scorer in `service.py` with a loaded ML model artifact (Lab 10 pattern).
- Add OpenTelemetry instrumentation (Lab 13 pattern).
- Add Azure Managed Identity for secret access instead of environment variables.
- Set `minReplicas: 1` if cold-start latency is unacceptable.

## Tradeoffs

- Rule-based scorer instead of a trained model keeps the lab focused on the API and deployment path, not model training.
- No authentication: acceptable for a portfolio demo, not for a real service.
- Single service, no background workers or queues.

## Evidence

- [ ] `uv run ... pytest` passes
- [ ] `tox -e lint,type,py312` passes
- [ ] `docker build` succeeds
- [ ] `/health` works inside container
- [ ] Azure deployment workflow in `.github/workflows/deploy-azure-container-app.yml`
