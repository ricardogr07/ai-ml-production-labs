from __future__ import annotations

from pydantic import BaseModel, Field


class Document(BaseModel):
    id: str
    content: str
    category: str = ""
    embedding: list[float] = Field(default_factory=list)


class RetrievalResult(BaseModel):
    doc_id: str
    content: str
    score: float
