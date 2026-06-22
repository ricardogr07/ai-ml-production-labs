from __future__ import annotations

from azure_functions_text_classifier.classifier import classify_text
from azure_functions_text_classifier.schemas import ClassifyRequest, ClassifyResponse
from production_labs_shared.telemetry import timed_operation


class ClassifierService:
    def classify(self, request: ClassifyRequest) -> ClassifyResponse:
        with timed_operation("classify", text_length=len(request.text)):
            result = classify_text(request.text)
        return ClassifyResponse(**result)
