from typing import Literal

from pydantic import BaseModel, Field

ProjectLabel = Literal[
    "cloud_api", "ml_model", "rag_system", "agent_system", "data_pipeline", "observability"
]


class ProjectRequest(BaseModel):
    description: str = Field(min_length=1, max_length=5000)


class ProjectResponse(BaseModel):
    label: ProjectLabel
    confidence: float = Field(ge=0.0, le=1.0)
    model_version: str
