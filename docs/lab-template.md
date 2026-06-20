# Lab NN: Project Name

## What this proves

One clear paragraph explaining the production or AI/ML capability.

## Scope

This lab intentionally does one thing:

- Capability:
- Input:
- Output:
- Deployment target:
- Non-goals:

## Architecture

```text
client -> API/function/agent -> service layer -> model/storage/tool -> response
```

## Tech stack

- Python 3.12
- uv workspace
- tox + tox-uv
- pytest
- ruff
- pyrefly
- Docker
- Terraform
- Azure target, if applicable

## Run locally

```bash
uv sync
uv run --package PACKAGE_NAME pytest
uv run --package PACKAGE_NAME uvicorn PACKAGE_NAME.app:app --reload
```

## Test

```bash
tox -e lint,type,py312
```

## Docker

```bash
docker build -t PROJECT_NAME:local .
docker run --rm -p 8000:8000 --env-file .env.example PROJECT_NAME:local
```

## API examples

Request and response examples.

## Evaluation

Model metrics, retrieval metrics, latency, or smoke-test result.

## Production notes

What would change for real production.

## Tradeoffs

What was intentionally simplified.

## Evidence

- Local test screenshot or output.
- Docker run output.
- Azure URL, if deployed.
- Observability screenshot, if applicable.
