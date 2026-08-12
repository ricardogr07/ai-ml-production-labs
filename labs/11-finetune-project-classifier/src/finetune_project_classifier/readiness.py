from finetune_project_classifier.errors import ModelNotReadyError
from finetune_project_classifier.service import load_model


def readiness() -> dict[str, str]:
    try:
        load_model()
    except ModelNotReadyError as exc:
        return {"model": str(exc)}
    return {"model": "ok"}
