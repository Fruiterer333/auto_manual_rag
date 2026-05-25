from typing import Literal

from pydantic import BaseModel, Field


ContentType = Literal["normal", "warning", "caution", "note", "procedure", "table"]
RiskLevel = Literal["low", "medium", "high", "critical"]


class Document(BaseModel):
    source_file: str
    title: str | None = None
    page_count: int | None = None
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class Chunk(BaseModel):
    id: str
    text: str
    source_file: str
    page: int | None = None
    chapter: str | None = None
    section: str | None = None
    content_type: ContentType = "normal"
    risk_level: RiskLevel = "low"
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class Citation(BaseModel):
    source_file: str
    page: int | None = None
    chapter: str | None = None
    section: str | None = None
    chunk_id: str | None = None
    quote: str | None = None


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)


class QueryResponse(BaseModel):
    question: str
    answer: str
    citations: list[Citation] = Field(default_factory=list)
