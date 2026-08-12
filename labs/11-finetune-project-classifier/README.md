# Lab 11: Fine-tuned Project Classifier

## What this proves

A small Hugging Face classifier fine-tuned on labeled project descriptions, evaluated, saved locally, and served through FastAPI.

## Scope

- Input: project description text
- Output: one of `cloud_api`, `ml_model`, `rag_system`, `agent_system`, `data_pipeline`, `observability`
- Model: `distilbert-base-uncased`
- Target: local CPU or GPU
- Non-goals: registry, production data, online training

## Run locally

```bash
uv sync
uv run --package finetune-project-classifier python labs/11-finetune-project-classifier/scripts/finetune.py
uv run --package finetune-project-classifier uvicorn finetune_project_classifier.app:app --app-dir labs/11-finetune-project-classifier/src --reload
```

Training writes `artifacts/project-classifier` and `metrics.json`. The first run downloads the base model.

## API

```bash
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d '{"description":"A FastAPI service with OpenAPI and health checks"}'
```

## Docker Compose

```bash
docker compose up --build
```

The image trains the sample dataset during build, then starts the API on port `8000`. Run `docker compose run --rm train` to retrain into the mounted model volume.

## Tests and quality

```bash
uv run --package finetune-project-classifier pytest labs/11-finetune-project-classifier/tests
ruff check labs/11-finetune-project-classifier
pyrefly check labs/11-finetune-project-classifier/src
```

## Tradeoffs

The dataset has 18 synthetic examples. It demonstrates the workflow, not production accuracy. Real use needs a larger labeled corpus, held-out evaluation, model versioning, and monitoring.
