from pydantic import BaseModel, Field


MetadataValue = str | int | float | bool | None | list[str] | list[int]


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
    subsection: str | None = None
    content_type: str | None = None
    risk_level: str | None = None
    metadata: dict[str, MetadataValue] = Field(default_factory=dict)


class ManualBlock(BaseModel):
    block_id: str
    source_file: str
    text: str
    start_page: int | None = None
    end_page: int | None = None
    chapter: str | None = None
    section: str | None = None
    subsection: str | None = None
    heading_path: list[str] = Field(default_factory=list)
    content_type: str | None = None
    risk_level: str | None = None
    metadata: dict[str, MetadataValue] = Field(default_factory=dict)


class Citation(BaseModel):
    source_file: str
    page: int | None = None
    chunk_id: str
    quote: str
    score: float | None = None
    distance: float | None = None
    chapter: str | None = None
    section: str | None = None
    subsection: str | None = None
    content_type: str | None = None
    risk_level: str | None = None
    selection_score: float | None = None
    is_expanded_neighbor: bool = False
    retrieval_source: str | None = None
    dense_rank: int | None = None
    bm25_rank: int | None = None
    dense_score: float | None = None
    bm25_score: float | None = None
    rrf_score: float | None = None


class RetrievedChunk(BaseModel):
    chunk: Chunk
    score: float | None = None
    distance: float | None = None
    selection_score: float | None = None
    is_expanded_neighbor: bool = False


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    retrieval_mode: str | None = None


class QueryResponse(BaseModel):
    question: str
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    retrieval_mode: str | None = None
