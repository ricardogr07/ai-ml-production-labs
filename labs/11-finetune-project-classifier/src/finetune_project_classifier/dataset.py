"""Synthetic labeled dataset for project type classification."""

from __future__ import annotations

LABELS = ["cloud_api", "ml_model", "rag_system", "agent_system", "data_pipeline", "observability"]

LABEL_TO_ID = {label: i for i, label in enumerate(LABELS)}
ID_TO_LABEL = {i: label for label, i in LABEL_TO_ID.items()}

SAMPLES: list[tuple[str, str]] = [
    ("FastAPI service deployed to Azure Container Apps with health checks.", "cloud_api"),
    ("REST endpoint with Pydantic validation and OpenAPI schema.", "cloud_api"),
    ("Serverless Azure Function for text inference.", "cloud_api"),
    ("Train a Random Forest classifier on incident data with MLflow tracking.", "ml_model"),
    ("Scikit-learn pipeline with cross-validation and feature engineering.", "ml_model"),
    ("XGBoost model for churn prediction with SHAP explanations.", "ml_model"),
    ("RAG system with semantic chunking and metadata filtering.", "rag_system"),
    ("Vector search over document corpus with Recall@3 evaluation.", "rag_system"),
    ("LlamaIndex Q&A with cited source chunks.", "rag_system"),
    ("LangGraph agent with typed state and tool calls.", "agent_system"),
    ("Multi-step agentic workflow with controlled graph transitions.", "agent_system"),
    ("ReAct agent with web search and structured output.", "agent_system"),
    ("ETL pipeline ingesting JSON events into Cosmos DB.", "data_pipeline"),
    ("Batch feature engineering job with pandas and partitioned output.", "data_pipeline"),
    ("Streaming data processor with Kafka consumer.", "data_pipeline"),
    ("OpenTelemetry traces and metrics for a FastAPI service.", "observability"),
    ("Structured logging with structlog and correlation IDs.", "observability"),
    ("Application Insights integration with latency dashboards.", "observability"),
]
