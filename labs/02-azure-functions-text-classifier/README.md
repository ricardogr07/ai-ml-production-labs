# Lab 02: Azure Functions Text Classifier

## What this proves

Serverless Python inference endpoint using Azure Functions HTTP trigger. The classifier runs on demand with zero idle cost, demonstrating when serverless is the right deployment shape for small inference workloads.

## Scope and constraints

- **Capability:** Text classification via Azure Functions HTTP trigger (Python v2 model)
- **Input:** `POST /api/classify` with `{"text": "..."}`
- **Output:** `{"label": "...", "confidence": ..., "model_version": "..."}`
- **Deployment target:** Azure Functions, Consumption plan
- **Non-goals:** model training, model artifact storage, persistence, streaming, authentication

## Tech stack

| Component | Technology |
|-----------|-----------|
| Runtime | Python 3.12, Azure Functions v2 |
| Validation | Pydantic v2 |
| Logging | structlog (via production-labs-shared) |
| Telemetry | timed_operation (via production-labs-shared) |
| Config | pydantic-settings BaseLabSettings |
| Package manager | uv (workspace) |
| Tests | pytest, tox |

## Architecture

```text
client
  -> POST /api/classify
  -> Azure Function HTTP trigger (function_app.py)
  -> ClassifierService (service.py)
  -> classify_text() rule engine (classifier.py)
  -> ClassifyResponse (schemas.py)
  -> JSON response
```

See [docs/architecture.md](docs/architecture.md) for Mermaid diagrams and technology justification.

## Run locally

```bash
# Install dependencies
uv sync --all-packages

# Start the function host (requires Azure Functions Core Tools)
func start
```

The function will be available at `http://localhost:7071/api/classify`.

## API examples

**Classify an incident:**
```bash
curl -X POST http://localhost:7071/api/classify \
  -H "Content-Type: application/json" \
  -d '{"text": "Database connection failed in production."}'
```
```json
{"label": "incident", "confidence": 0.85, "model_version": "rules-v0.1.0"}
```

**Classify a deployment:**
```bash
curl -X POST http://localhost:7071/api/classify \
  -H "Content-Type: application/json" \
  -d '{"text": "New release deployed to staging environment."}'
```
```json
{"label": "deployment", "confidence": 0.75, "model_version": "rules-v0.1.0"}
```

**Classify general text:**
```bash
curl -X POST http://localhost:7071/api/classify \
  -H "Content-Type: application/json" \
  -d '{"text": "Weekly team standup notes."}'
```
```json
{"label": "general", "confidence": 0.6, "model_version": "rules-v0.1.0"}
```

**Validation error:**
```bash
curl -X POST http://localhost:7071/api/classify \
  -H "Content-Type: application/json" \
  -d '{"text": ""}'
```
```json
{"detail": "...", "request_id": ""}
```

## Test

```bash
# Run all tests for this lab
uv run --package azure-functions-text-classifier pytest labs/02-azure-functions-text-classifier/tests -v

# Full tox gate from repo root
tox -e lint,type,py312,security,audit
```

## Production notes

- **Cold starts:** Python Functions on Consumption incur ~500ms cold start on first request after idle. Use Premium plan or pre-warmed instances for latency-sensitive paths.
- **Classifier:** The current implementation is rule-based (no model artifact). A real deployment would load a scikit-learn or ONNX model from Azure Blob Storage or a mounted volume.
- **Auth:** The function runs with `AuthLevel.ANONYMOUS`. Production deployments should enable function-level or API-management auth.
- **Scaling:** Consumption plan scales horizontally per incoming request volume. Each instance is stateless; the classifier singleton is cheap to re-create.

## Tradeoffs vs Lab 01 (Container Apps)

Container Apps (Lab 01) is better when warm latency matters. Functions are better when near-zero idle cost matters and occasional cold starts are acceptable.
