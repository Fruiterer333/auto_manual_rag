import json
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from app.data.schemas.models import Citation, QueryResponse
from app.evaluation.answer_normalization import term_matches_answer
from app.evaluation.schemas import EvalEvidence
from app.rag.prompts.answer_prompt import PromptEvidenceSnapshot
from app.rag.utils.internal_evidence_refs import contains_internal_evidence_reference


STANDARD_INSUFFICIENT_ANSWER = "我没有在手册中找到可靠依据"
ANSWER_EVAL_SEMANTICS_VERSION = "v4.3"
ANSWER_CONTRACT_REVIEW_MARKER = "ANSWER_CONTRACT_REVIEW"
HUMAN_REVIEW_RUBRIC = {
    "groundedness": "事实与操作说明是否由实际 prompt Evidence 支持",
    "correctness": "是否准确表达手册事实、条件、方向和状态",
    "completeness": "是否覆盖回答问题所需的全部核心事实",
    "condition_handling": "是否保留关键前提、车辆状态和适用条件",
    "safety_preservation": "是否保留关键警告、禁止和安全动作",
    "unsupported_claim": "是否包含 prompt Evidence 无法支持的实质性事实陈述",
    "critical_safety_omission": "是否遗漏 answer contract 明确要求的关键安全动作或警告",
}


class AnswerEvalCase(BaseModel):
    id: str
    question: str
    answer_type: Literal[
        "procedure",
        "warning",
        "explanation",
        "parameter",
        "condition",
        "insufficient_evidence",
    ]
    must_include_terms: list[str] = Field(default_factory=list)
    must_include_points: list[str] = Field(default_factory=list)
    must_not_include_terms: list[str] = Field(default_factory=list)
    must_not_claim: list[str] = Field(default_factory=list)
    critical_warning_points: list[str] = Field(default_factory=list)
    expected_sections: list[str] = Field(default_factory=list)
    expected_subsections: list[str] = Field(default_factory=list)
    allow_insufficient_answer: bool = False
    evidence: list[EvalEvidence] = Field(default_factory=list)
    source_case_id: str | None = None
    split: str = "dev"
    notes: str = ""


class AnswerCitationRecord(BaseModel):
    page: int | None = None
    chapter: str | None = None
    section: str | None = None
    subsection: str | None = None
    chunk_id: str
    quote: str


class AnswerPromptEvidenceRecord(BaseModel):
    evidence_id: str
    order: int
    chunk_id: str
    page: int | None = None
    chapter: str | None = None
    section: str | None = None
    subsection: str | None = None
    heading_path: str
    text: str
    content_type: str
    truncated: bool
    original_text_chars: int
    prompt_text_chars: int


class DeterministicAnswerChecks(BaseModel):
    answer_non_empty: bool
    must_include_term_coverage: float | None = None
    matched_must_include_terms: list[str] = Field(default_factory=list)
    missing_must_include_terms: list[str] = Field(default_factory=list)
    forbidden_term_hits: list[str] = Field(default_factory=list)
    evidence_structure_hit: bool | None = None
    expected_section_hit: bool | None = None
    expected_subsection_hit: bool | None = None
    insufficient_evidence_behavior: bool | None = None
    internal_reference_leak: bool = False


class HumanAnswerReview(BaseModel):
    groundedness: int | None = Field(
        default=None,
        ge=0,
        le=2,
        description=HUMAN_REVIEW_RUBRIC["groundedness"],
    )
    correctness: int | None = Field(
        default=None,
        ge=0,
        le=2,
        description=HUMAN_REVIEW_RUBRIC["correctness"],
    )
    completeness: int | None = Field(
        default=None,
        ge=0,
        le=2,
        description=HUMAN_REVIEW_RUBRIC["completeness"],
    )
    condition_handling: int | None = Field(
        default=None,
        ge=0,
        le=2,
        description=HUMAN_REVIEW_RUBRIC["condition_handling"],
    )
    safety_preservation: int | None = Field(
        default=None,
        ge=0,
        le=2,
        description=HUMAN_REVIEW_RUBRIC["safety_preservation"],
    )
    unsupported_claim: bool | None = Field(
        default=None,
        description=HUMAN_REVIEW_RUBRIC["unsupported_claim"],
    )
    critical_safety_omission: bool | None = Field(
        default=None,
        description=HUMAN_REVIEW_RUBRIC["critical_safety_omission"],
    )
    notes: str | None = None


class AnswerCaseResult(BaseModel):
    case_id: str
    question: str
    source_case_id: str | None = None
    answer_type: str
    raw_answer: str | None = None
    final_answer: str
    retrieval_mode: str
    prompt_evidence: list[AnswerPromptEvidenceRecord] = Field(default_factory=list)
    citations: list[AnswerCitationRecord] = Field(default_factory=list)
    deterministic_checks: DeterministicAnswerChecks
    must_include_points: list[str] = Field(default_factory=list)
    must_not_claim: list[str] = Field(default_factory=list)
    critical_warning_points: list[str] = Field(default_factory=list)
    human_review: HumanAnswerReview = Field(default_factory=HumanAnswerReview)
    elapsed_seconds: float

    @model_validator(mode="before")
    @classmethod
    def load_legacy_answer_field(cls, value: Any) -> Any:
        if isinstance(value, dict) and "final_answer" not in value and "answer" in value:
            value = dict(value)
            value["final_answer"] = value["answer"]
        return value


class AnswerEvaluationRun(BaseModel):
    generated_at: str
    dataset_path: str
    case_count: int
    semantics_version: str = ANSWER_EVAL_SEMANTICS_VERSION
    config: dict[str, Any] = Field(default_factory=dict)
    summary: dict[str, float | int | None] = Field(default_factory=dict)
    results: list[AnswerCaseResult] = Field(default_factory=list)


class AnswerSemanticsValidationResult(BaseModel):
    semantics_version: str
    valid: bool
    rubric_schema_valid: bool
    outstanding_contract_reviews: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)


def load_answer_eval_cases(
    dataset_path: str | Path,
    *,
    limit: int | None = None,
    split: str | None = "dev",
) -> list[AnswerEvalCase]:
    path = Path(dataset_path)
    if not path.exists():
        raise FileNotFoundError(f"Answer evaluation dataset not found: {path}")

    cases: list[AnswerEvalCase] = []
    seen_ids: set[str] = set()
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}: {exc}") from exc
            try:
                case = AnswerEvalCase(**payload)
            except Exception as exc:
                raise ValueError(f"Invalid answer eval case at {path}:{line_number}: {exc}") from exc
            if case.id in seen_ids:
                raise ValueError(f"Duplicate answer eval case id at {path}:{line_number}: {case.id}")
            seen_ids.add(case.id)
            if split and case.split != split:
                continue
            cases.append(case)
            if limit is not None and len(cases) >= limit:
                break
    return cases


def evaluate_answer_response(
    case: AnswerEvalCase,
    response: QueryResponse,
    *,
    elapsed_seconds: float,
    retrieval_mode: str,
    raw_answer: str | None = None,
    prompt_evidence: Sequence[PromptEvidenceSnapshot] = (),
) -> AnswerCaseResult:
    answer = response.answer.strip()
    matched_terms = [
        term
        for term in case.must_include_terms
        if term and term_matches_answer(term, answer)
    ]
    missing_terms = [
        term
        for term in case.must_include_terms
        if term and not term_matches_answer(term, answer)
    ]
    term_coverage = (
        len(matched_terms) / len(case.must_include_terms)
        if case.must_include_terms
        else None
    )
    forbidden_hits = [
        term
        for term in case.must_not_include_terms
        if term and term_matches_answer(term, answer)
    ]
    section_hit = _citation_field_hit(response.citations, "section", case.expected_sections)
    subsection_hit = _citation_field_hit(
        response.citations,
        "subsection",
        case.expected_subsections,
    )
    structure_checks = [value for value in (section_hit, subsection_hit) if value is not None]
    structure_hit = all(structure_checks) if structure_checks else None
    insufficient_behavior = (
        STANDARD_INSUFFICIENT_ANSWER in answer
        if case.allow_insufficient_answer
        else None
    )
    checks = DeterministicAnswerChecks(
        answer_non_empty=bool(answer),
        must_include_term_coverage=term_coverage,
        matched_must_include_terms=matched_terms,
        missing_must_include_terms=missing_terms,
        forbidden_term_hits=forbidden_hits,
        evidence_structure_hit=structure_hit,
        expected_section_hit=section_hit,
        expected_subsection_hit=subsection_hit,
        insufficient_evidence_behavior=insufficient_behavior,
        internal_reference_leak=has_internal_reference_leak(answer),
    )
    return AnswerCaseResult(
        case_id=case.id,
        question=case.question,
        source_case_id=case.source_case_id,
        answer_type=case.answer_type,
        raw_answer=raw_answer,
        final_answer=response.answer,
        retrieval_mode=response.retrieval_mode or retrieval_mode,
        prompt_evidence=[
            _prompt_evidence_record(evidence) for evidence in prompt_evidence
        ],
        citations=[_citation_record(citation) for citation in response.citations],
        deterministic_checks=checks,
        must_include_points=case.must_include_points,
        must_not_claim=case.must_not_claim,
        critical_warning_points=case.critical_warning_points,
        elapsed_seconds=elapsed_seconds,
    )


def has_internal_reference_leak(answer: str) -> bool:
    return contains_internal_evidence_reference(answer)


def build_answer_evaluation_run(
    *,
    dataset_path: str,
    config: dict[str, Any],
    results: list[AnswerCaseResult],
) -> AnswerEvaluationRun:
    return AnswerEvaluationRun(
        generated_at=datetime.now().isoformat(timespec="seconds"),
        dataset_path=dataset_path,
        case_count=len(results),
        semantics_version=ANSWER_EVAL_SEMANTICS_VERSION,
        config=config,
        summary=summarize_answer_results(results),
        results=results,
    )


def validate_answer_eval_semantics(
    cases: list[AnswerEvalCase],
) -> AnswerSemanticsValidationResult:
    expected_rubric_fields = set(HUMAN_REVIEW_RUBRIC)
    actual_rubric_fields = set(HumanAnswerReview.model_fields) - {"notes"}
    rubric_schema_valid = expected_rubric_fields == actual_rubric_fields
    outstanding_reviews = [
        case.id for case in cases if ANSWER_CONTRACT_REVIEW_MARKER in case.notes
    ]
    issues: list[str] = []
    if not ANSWER_EVAL_SEMANTICS_VERSION:
        issues.append("missing_semantics_version")
    if not rubric_schema_valid:
        issues.append("human_review_rubric_schema_mismatch")
    if outstanding_reviews:
        issues.append("outstanding_answer_contract_review")
    return AnswerSemanticsValidationResult(
        semantics_version=ANSWER_EVAL_SEMANTICS_VERSION,
        valid=not issues,
        rubric_schema_valid=rubric_schema_valid,
        outstanding_contract_reviews=outstanding_reviews,
        issues=issues,
    )


def ensure_answer_eval_semantics_valid(
    cases: list[AnswerEvalCase],
) -> AnswerSemanticsValidationResult:
    result = validate_answer_eval_semantics(cases)
    if not result.valid:
        raise ValueError(
            "Answer evaluation semantics are not frozen: "
            f"version={result.semantics_version} issues={result.issues} "
            f"outstanding_contract_reviews={result.outstanding_contract_reviews}"
        )
    return result


def summarize_answer_results(
    results: list[AnswerCaseResult],
) -> dict[str, float | int | None]:
    term_coverages = [
        result.deterministic_checks.must_include_term_coverage
        for result in results
        if result.deterministic_checks.must_include_term_coverage is not None
    ]
    structure_hits = [
        result.deterministic_checks.evidence_structure_hit
        for result in results
        if result.deterministic_checks.evidence_structure_hit is not None
    ]
    insufficient_checks = [
        result.deterministic_checks.insufficient_evidence_behavior
        for result in results
        if result.deterministic_checks.insufficient_evidence_behavior is not None
    ]
    return {
        "case_count": len(results),
        "answer_non_empty_pass": sum(
            result.deterministic_checks.answer_non_empty for result in results
        ),
        "internal_reference_leak_count": sum(
            result.deterministic_checks.internal_reference_leak for result in results
        ),
        "forbidden_term_failure_count": sum(
            bool(result.deterministic_checks.forbidden_term_hits) for result in results
        ),
        "must_include_term_average_coverage": (
            mean(term_coverages) if term_coverages else None
        ),
        "expected_evidence_hit_rate": (
            mean(float(value) for value in structure_hits) if structure_hits else None
        ),
        "insufficient_evidence_behavior_pass_rate": (
            mean(float(value) for value in insufficient_checks)
            if insufficient_checks
            else None
        ),
        "average_elapsed_seconds": (
            mean(result.elapsed_seconds for result in results) if results else None
        ),
    }


def render_answer_evaluation_markdown(run: AnswerEvaluationRun) -> str:
    lines = [
        "# Answer Generation Evaluation",
        "",
        "## Run Configuration",
        "",
        f"- generated_at: {run.generated_at}",
        f"- dataset: `{run.dataset_path}`",
        f"- case_count: {run.case_count}",
        f"- semantics_version: {run.semantics_version}",
    ]
    for key, value in run.config.items():
        lines.append(f"- {key}: {_display(value)}")
    lines.extend(["", "## Summary", "", "| metric | value |", "| --- | ---: |"])
    for key, value in run.summary.items():
        lines.append(f"| {key} | {_display(value)} |")
    lines.extend(
        [
            "",
            "## Manual Review Status",
            "",
            "Human semantic review has not been completed.",
            "",
            "Deterministic checks do not establish semantic correctness, groundedness, or completeness.",
            "",
            "## Case Details",
        ]
    )
    for result in run.results:
        lines.extend(_case_markdown(result))
    return "\n".join(lines)


def write_answer_evaluation_outputs(
    run: AnswerEvaluationRun,
    *,
    markdown_path: str | Path,
    json_path: str | Path,
) -> tuple[Path, Path]:
    md_path = Path(markdown_path)
    structured_path = Path(json_path)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    structured_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(render_answer_evaluation_markdown(run), encoding="utf-8")
    structured_path.write_text(
        json.dumps(run.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return md_path, structured_path


def _citation_field_hit(
    citations: list[Citation],
    field: Literal["section", "subsection"],
    expected_values: list[str],
) -> bool | None:
    if not expected_values:
        return None
    return any(
        _matches_expected(getattr(citation, field), expected_values)
        for citation in citations
    )


def _matches_expected(actual: str | None, expected_values: list[str]) -> bool:
    if not actual:
        return False
    return any(expected in actual or actual in expected for expected in expected_values)


def _citation_record(citation: Citation) -> AnswerCitationRecord:
    return AnswerCitationRecord(
        page=citation.page,
        chapter=citation.chapter,
        section=citation.section,
        subsection=citation.subsection,
        chunk_id=citation.chunk_id,
        quote=citation.quote,
    )


def _prompt_evidence_record(
    evidence: PromptEvidenceSnapshot,
) -> AnswerPromptEvidenceRecord:
    return AnswerPromptEvidenceRecord(
        evidence_id=evidence.evidence_id,
        order=evidence.order,
        chunk_id=evidence.chunk_id,
        page=evidence.page,
        chapter=evidence.chapter,
        section=evidence.section,
        subsection=evidence.subsection,
        heading_path=evidence.heading_path,
        text=evidence.text,
        content_type=evidence.content_type,
        truncated=evidence.truncated,
        original_text_chars=evidence.original_text_chars,
        prompt_text_chars=evidence.prompt_text_chars,
    )


def _case_markdown(result: AnswerCaseResult) -> list[str]:
    checks = result.deterministic_checks
    lines = [
        "",
        f"### {result.case_id}",
        "",
        f"**Question:** {result.question}",
        "",
        f"**Answer type:** {result.answer_type}",
        "",
        f"**Source case:** {_display(result.source_case_id)}",
        "",
        "**Raw answer:**",
        "",
        result.raw_answer if result.raw_answer is not None else "_NOT_GENERATED_OR_NOT_CAPTURED_",
        "",
        "**Final answer:**",
        "",
        result.final_answer or "_EMPTY_",
        "",
        "**Prompt Evidence:**",
        "",
    ]
    if result.prompt_evidence:
        for evidence in result.prompt_evidence:
            lines.extend(
                [
                    "- "
                    f"{evidence.evidence_id}; order={evidence.order}; "
                    f"chunk_id={evidence.chunk_id}; page={_display(evidence.page)}; "
                    f"chapter={_display(evidence.chapter)}; "
                    f"section={_display(evidence.section)}; "
                    f"subsection={_display(evidence.subsection)}; "
                    f"heading_path={evidence.heading_path}; "
                    f"content_type={evidence.content_type}; "
                    f"truncated={evidence.truncated}; "
                    f"original_text_chars={evidence.original_text_chars}; "
                    f"prompt_text_chars={evidence.prompt_text_chars}",
                    "",
                    evidence.text,
                    "",
                ]
            )
    else:
        lines.extend(["- N/A", ""])
    lines.extend(
        [
            "**Citations:**",
            "",
        ]
    )
    if result.citations:
        for citation in result.citations:
            lines.append(
                "- "
                f"page={_display(citation.page)}; "
                f"chapter={_display(citation.chapter)}; "
                f"section={_display(citation.section)}; "
                f"subsection={_display(citation.subsection)}; "
                f"chunk_id={citation.chunk_id}; quote={citation.quote}"
            )
    else:
        lines.append("- N/A")
    lines.extend(
        [
            "",
            "**Deterministic checks:**",
            "",
            f"- answer_non_empty: {checks.answer_non_empty}",
            f"- must_include_term_coverage: {_display(checks.must_include_term_coverage)}",
            f"- matched_must_include_terms: {_list_display(checks.matched_must_include_terms)}",
            f"- missing_must_include_terms: {_list_display(checks.missing_must_include_terms)}",
            f"- forbidden_term_hits: {_list_display(checks.forbidden_term_hits)}",
            f"- evidence_structure_hit: {_display(checks.evidence_structure_hit)}",
            f"- expected_section_hit: {_display(checks.expected_section_hit)}",
            f"- expected_subsection_hit: {_display(checks.expected_subsection_hit)}",
            f"- insufficient_evidence_behavior: {_display(checks.insufficient_evidence_behavior)}",
            f"- internal_reference_leak: {checks.internal_reference_leak}",
            "",
            f"**Must include points:** {_list_display(result.must_include_points)}",
            "",
            f"**Must not claim:** {_list_display(result.must_not_claim)}",
            "",
            f"**Critical warning points:** {_list_display(result.critical_warning_points)}",
            "",
            "**Human review:**",
            "",
            "- Groundedness: TODO / NOT REVIEWED",
            "- Correctness: TODO / NOT REVIEWED",
            "- Completeness: TODO / NOT REVIEWED",
            "- Condition Handling: TODO / NOT REVIEWED",
            (
                "- Safety Preservation: TODO / NOT REVIEWED"
                if result.answer_type == "warning" or result.critical_warning_points
                else "- Safety Preservation: N/A"
            ),
            "- Unsupported claim: TODO / NOT REVIEWED",
            "- Critical safety omission: TODO / NOT REVIEWED",
            "- Notes: TODO / NOT REVIEWED",
            "",
            f"**Elapsed seconds:** {result.elapsed_seconds:.4f}",
        ]
    )
    return lines


def _list_display(values: list[str]) -> str:
    return "; ".join(values) if values else "N/A"


def _display(value: object) -> str:
    if value is None or value == "":
        return "N/A"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)
