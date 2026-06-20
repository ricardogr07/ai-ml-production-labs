"""FastAPI service with OpenTelemetry instrumentation."""

from __future__ import annotations

from collections.abc import Callable
import uuid

from fastapi import FastAPI, Request, Response
from opentelemetry import metrics, trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from production_labs_shared.health import HealthResponse
from production_labs_shared.logging import configure_logging

from fastapi_opentelemetry_lab.telemetry import configure_telemetry

SERVICE_NAME = "fastapi-opentelemetry-lab"
SERVICE_VERSION = "0.1.0"

configure_logging()
configure_telemetry(SERVICE_NAME)

app = FastAPI(title=SERVICE_NAME, version=SERVICE_VERSION)
FastAPIInstrumentor.instrument_app(app)

tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)
request_counter = meter.create_counter("http_requests_total", description="Total HTTP requests")
error_counter = meter.create_counter("http_errors_total", description="Total HTTP errors")


@app.middleware("http")
async def request_id_middleware(request: Request, call_next: Callable) -> Response:
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response: Response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    request_counter.add(1, {"route": "/health"})
    return HealthResponse(service=SERVICE_NAME, version=SERVICE_VERSION)


@app.get("/work")
def do_work() -> dict[str, str]:
    with tracer.start_as_current_span("do_work"):
        request_counter.add(1, {"route": "/work"})
        return {"result": "done"}
