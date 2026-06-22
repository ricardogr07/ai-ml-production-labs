"""Azure Functions HTTP trigger for text classification."""

from __future__ import annotations

import azure.functions as func
from pydantic import ValidationError

from azure_functions_text_classifier.config import settings
from azure_functions_text_classifier.schemas import ClassifyRequest
from azure_functions_text_classifier.service import ClassifierService
from production_labs_shared.logging import configure_logging
from production_labs_shared.schemas import ErrorResponse

configure_logging(settings.log_level)

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

_service = ClassifierService()


@app.route(route="classify", methods=["POST"])
def classify(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
    except ValueError:
        err = ErrorResponse(detail="Request body must be valid JSON")
        return func.HttpResponse(
            err.model_dump_json(), status_code=400, mimetype="application/json"
        )

    try:
        request = ClassifyRequest(**body)
    except (ValidationError, TypeError) as exc:
        err = ErrorResponse(detail=str(exc))
        return func.HttpResponse(
            err.model_dump_json(), status_code=422, mimetype="application/json"
        )

    result = _service.classify(request)
    return func.HttpResponse(result.model_dump_json(), mimetype="application/json")
