from __future__ import annotations

from pydantic import BaseModel, Field


class Document(BaseModel):
    id: str
    content: str
    source: str = ""
    embedding: list[float] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)


class SearchResult(BaseModel):
    document: Document
    score: float = Field(ge=-1.0, le=1.0)
