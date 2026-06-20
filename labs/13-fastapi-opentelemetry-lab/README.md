# Lab 13: FastAPI OpenTelemetry Lab

## What this proves

A FastAPI service fully instrumented with OpenTelemetry: distributed traces (spans), request metrics (counter), structured logs with request IDs, and a middleware that propagates correlation IDs through every response. Local console exporters make traces visible without a collector.

## Scope

- Capability: Traces, metrics, and structured logs for a FastAPI service
- Input: any HTTP request
- Output: OTel spans to console + metrics + structured log with request ID
- Deployment target: Azure Container Apps + Application Insights (optional)
- Non-goals: distributed tracing across multiple services, alerting rules

## Architecture

```text
client → FastAPI (OTel instrumented)
              ↓
         OTel SDK
         ├── traces → ConsoleSpanExporter (local) / Azure Monitor (prod)
         ├── metrics → ConsoleMetricExporter (local) / Azure Monitor (prod)
         └── logs → structlog (JSON)
```

## Run locally

```bash
uv sync
uv run --package fastapi-opentelemetry-lab uvicorn fastapi_opentelemetry_lab.app:app --reload
# Traces and metrics print to console
```

## Test

```bash
uv run --package fastapi-opentelemetry-lab pytest labs/13-fastapi-opentelemetry-lab/tests
```

## Docker

```bash
docker build -f labs/13-fastapi-opentelemetry-lab/Dockerfile -t fastapi-opentelemetry-lab:local .
docker run --rm -p 8000:8000 fastapi-opentelemetry-lab:local
```

## Tradeoffs

- Console exporters: no collector or Azure account needed locally. Swap for `azure-monitor-opentelemetry` for production.
- `PeriodicExportingMetricReader` at 10s interval keeps console output readable during development.
- No sampling configuration: all traces are exported. Production would set `TraceIdRatioBased` sampling.
