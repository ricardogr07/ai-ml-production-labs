# Lab 02: Architecture

## Request Flow

```mermaid
sequenceDiagram
    participant Client
    participant AzureFunction as Azure Function (HTTP Trigger)
    participant ClassifierService
    participant classify_text as classify_text()

    Client->>AzureFunction: POST /api/classify {"text": "..."}
    AzureFunction->>AzureFunction: parse JSON body
    alt invalid JSON
        AzureFunction-->>Client: 400 {"detail": "..."}
    end
    AzureFunction->>AzureFunction: validate ClassifyRequest (Pydantic)
    alt validation error
        AzureFunction-->>Client: 422 {"detail": "..."}
    end
    AzureFunction->>ClassifierService: classify(ClassifyRequest)
    ClassifierService->>classify_text: classify_text(text)
    classify_text-->>ClassifierService: {"label", "confidence", "model_version"}
    ClassifierService-->>AzureFunction: ClassifyResponse
    AzureFunction-->>Client: 200 {"label": "...", "confidence": ..., "model_version": "..."}
```

## Layer Diagram

```mermaid
graph TD
    subgraph Azure Functions Runtime
        trigger["HTTP Trigger (function_app.py)"]
    end

    subgraph Application Layer
        service["ClassifierService (service.py)"]
        schemas["Pydantic Schemas (schemas.py)"]
        config["Settings / BaseLabSettings (config.py)"]
        classifier["Rule Engine (classifier.py)"]
    end

    subgraph Shared Utilities
        logging["configure_logging"]
        telemetry["timed_operation"]
        error["ErrorResponse"]
    end

    trigger --> schemas
    trigger --> service
    trigger --> error
    service --> classifier
    service --> telemetry
    trigger --> config
    config --> logging
```

## Technology Choices

| Choice | Rationale |
|--------|-----------|
| Azure Functions (Consumption plan) | Near-zero idle cost; scales to zero between requests. Right for low-traffic, bursty inference workloads where warm latency is acceptable. |
| Python v2 programming model | Decorator-based routing (`@app.route`) keeps the function definition and binding together, reducing boilerplate. |
| Pydantic v2 validation | Consistent with the rest of the monorepo; provides free input validation, clear error messages, and typed response serialization. |
| Rule-based classifier | Keeps lab scope on the Functions deployment pattern, not model artifacts or training pipelines. |
| `production-labs-shared` | Centralizes config, logging, telemetry, and error schemas so labs stay thin and consistent. |

## Tradeoffs vs Lab 01 (Container Apps)

| Concern | Azure Functions | Azure Container Apps |
|---------|-----------------|----------------------|
| Idle cost | Near-zero (Consumption plan) | Scales to zero but has minimum replicas option |
| Cold start | ~500ms (Python) | Negligible once warm |
| Request duration limit | 5 min (Consumption) | Unlimited |
| Best fit | Bursty, latency-tolerant workloads | Sustained traffic, low-latency requirements |
