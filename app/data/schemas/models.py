from pydantic import BaseModel, Field


MetadataValue = str | int | float | bool | None


class Document(BaseModel):
    doc_id: str
    source_file: str
    page: int
    text: str
    metadata: dict[str, MetadataValue] = Field(default_factory=dict)


class Chunk(BaseModel):
    chunk_id: str
    doc_id: str
    source_file: str
    text: str
    page: int | None = None
    chapter: str | None = None
    section: str | None = None
    content_type: str | None = None
    risk_level: str | None = None
    metadata: dict[str, MetadataValue] = Field(default_factory=dict)


class Citation(BaseModel):
    source_file: str
    page: int | None = None
    chunk_id: str
    quote: str


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class QueryResponse(BaseModel):
    question: str
    answer: str
    citations: list[Citation] = Field(default_factory=list)
