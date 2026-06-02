from typing import Any

from pydantic import BaseModel, Field


class EvalEvidence(BaseModel):
    page: int | None = None
    section: str | None = None
    chunk_id: str | None = None
    quote: str = ""


class EvalCase(BaseModel):
    id: str
    question: str
    category: str
    intent_type: str
    expected_pages: list[int] = Field(default_factory=list)
    expected_sections: list[str] = Field(default_factory=list)
    acceptable_sections: list[str] = Field(default_factory=list)
    expected_content_types: list[str] = Field(default_factory=list)
    must_contain_terms: list[str] = Field(default_factory=list)
    answer_must_cover: list[str] = Field(default_factory=list)
    forbidden_content: list[str] = Field(default_factory=list)
    evidence: list[EvalEvidence] = Field(default_factory=list)
    split: str = "dev"
    notes: str = ""


class RetrievalHitDetail(BaseModel):
    rank: int
    chunk_id: str
    page: int | None = None
    section: str | None = None
    score: float | None = None
    evidence_hit: bool = False


class RetrievalEvalResult(BaseModel):
    case_id: str
    question: str
    category: str
    intent_type: str
    retrieval_mode: str
    top_k: int
    use_context_selection: bool = False
    metrics: dict[str, float | int | bool | None] = Field(default_factory=dict)
    raw_hits: list[RetrievalHitDetail] = Field(default_factory=list)
    final_hits: list[RetrievalHitDetail] = Field(default_factory=list)
    failure_reasons: list[str] = Field(default_factory=list)


class AnswerEvalResult(BaseModel):
    case_id: str
    question: str
    retrieval_mode: str
    answer: str = ""
    answer_coverage_ratio: float | None = None
    forbidden_content_hits: list[str] = Field(default_factory=list)
    has_citations: bool | None = None
    internal_reference_leak: bool | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvalSummary(BaseModel):
    dataset_path: str
    case_count: int
    retrieval_modes: list[str] = Field(default_factory=list)
    top_k: int
    use_context_selection: bool = False
    rerank_enabled: bool = False
    rerank_model_name: str | None = None
    rerank_top_n: int | None = None
    rerank_output_top_k: int | None = None
    overall_metrics: dict[str, float | int | None] = Field(default_factory=dict)
    by_retrieval_mode: dict[str, dict[str, float | int | None]] = Field(default_factory=dict)
    by_category: dict[str, dict[str, float | int | None]] = Field(default_factory=dict)
    by_intent_type: dict[str, dict[str, float | int | None]] = Field(default_factory=dict)
    results: list[RetrievalEvalResult] = Field(default_factory=list)
