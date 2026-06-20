"""Azure Functions HTTP trigger for text classification."""

from __future__ import annotations

import azure.functions as func

from azure_functions_text_classifier.classifier import classify_text

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="classify", methods=["POST"])
def classify(req: func.HttpRequest) -> func.HttpResponse:
    body = req.get_json()
    text = body.get("text", "")
    if not text:
        return func.HttpResponse('{"detail": "text is required"}', status_code=422, mimetype="application/json")

    result = classify_text(text)
    import json

    return func.HttpResponse(json.dumps(result), mimetype="application/json")
