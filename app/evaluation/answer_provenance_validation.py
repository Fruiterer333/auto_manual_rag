import re
from collections import Counter
from typing import Any

from pydantic import BaseModel, Field

from app.data.schemas.models import Chunk
from app.evaluation.answer_evaluator import AnswerEvalCase
from app.evaluation.schemas import EvalCase, EvalEvidence


class AnswerProvenanceIssue(BaseModel):
    case_id: str
    evidence_index: int | None
    issue_type: str
    expected: Any = None
    actual: Any = None


class AnswerProvenanceValidationResult(BaseModel):
    case_count: int
    positive_case_count: int
    hard_negative_case_count: int
    evidence_count: int
    valid: bool
    issue_counts: dict[str, int] = Field(default_factory=dict)
    issues: list[AnswerProvenanceIssue] = Field(default_factory=list)


def validate_answer_eval_provenance(
    cases: list[AnswerEvalCase],
    retrieval_cases: list[EvalCase],
    chunks: list[Chunk],
) -> AnswerProvenanceValidationResult:
    retrieval_by_id = {case.id: case for case in retrieval_cases}
    chunks_by_id = {chunk.chunk_id: chunk for chunk in chunks}
    issues: list[AnswerProvenanceIssue] = []
    seen_case_ids: set[str] = set()
    positive_case_count = 0
    hard_negative_case_count = 0
    evidence_count = 0

    for case in cases:
        if case.id in seen_case_ids:
            issues.append(_issue(case.id, None, "duplicate_case_id", "unique", case.id))
        seen_case_ids.add(case.id)

        is_hard_negative = case.answer_type == "insufficient_evidence"
        if is_hard_negative:
            hard_negative_case_count += 1
            issues.extend(_validate_hard_negative(case))
            continue

        positive_case_count += 1
        source_case = retrieval_by_id.get(case.source_case_id or "")
        if source_case is None:
            issues.append(
                _issue(
                    case.id,
                    None,
                    "source_case_not_found",
                    case.source_case_id or "non-empty source_case_id",
                    None,
                )
            )
        elif source_case.excluded:
            issues.append(
                _issue(
                    case.id,
                    None,
                    "source_case_excluded",
                    "active retrieval case",
                    source_case.id,
                )
            )

        if not case.evidence:
            issues.append(_issue(case.id, None, "missing_answer_evidence", "non-empty", []))
            continue

        for evidence_index, evidence in enumerate(case.evidence):
            evidence_count += 1
            issues.extend(
                _validate_evidence(
                    case.id,
                    evidence_index,
                    evidence,
                    chunks_by_id,
                )
            )

    counts = Counter(issue.issue_type for issue in issues)
    return AnswerProvenanceValidationResult(
        case_count=len(cases),
        positive_case_count=positive_case_count,
        hard_negative_case_count=hard_negative_case_count,
        evidence_count=evidence_count,
        valid=not issues,
        issue_counts=dict(counts),
        issues=issues,
    )


def ensure_answer_eval_provenance_valid(
    cases: list[AnswerEvalCase],
    retrieval_cases: list[EvalCase],
    chunks: list[Chunk],
) -> AnswerProvenanceValidationResult:
    result = validate_answer_eval_provenance(cases, retrieval_cases, chunks)
    if not result.valid:
        raise ValueError(format_answer_provenance_failure(result))
    return result


def format_answer_provenance_failure(
    result: AnswerProvenanceValidationResult,
    limit: int = 20,
) -> str:
    details = "; ".join(
        f"case={issue.case_id} evidence={issue.evidence_index} "
        f"type={issue.issue_type} expected={issue.expected!r} actual={issue.actual!r}"
        for issue in result.issues[:limit]
    )
    remaining = len(result.issues) - limit
    suffix = f"; ... {remaining} more" if remaining > 0 else ""
    return (
        "Answer evaluation provenance is inconsistent with the current corpus: "
        f"issues={len(result.issues)} counts={result.issue_counts}. {details}{suffix}"
    )


def _validate_hard_negative(case: AnswerEvalCase) -> list[AnswerProvenanceIssue]:
    issues: list[AnswerProvenanceIssue] = []
    if not case.allow_insufficient_answer:
        issues.append(
            _issue(
                case.id,
                None,
                "hard_negative_not_allowed_insufficient",
                True,
                case.allow_insufficient_answer,
            )
        )
    if case.evidence:
        issues.append(
            _issue(
                case.id,
                None,
                "hard_negative_has_evidence",
                [],
                [evidence.chunk_id for evidence in case.evidence],
            )
        )
    return issues


def _validate_evidence(
    case_id: str,
    evidence_index: int,
    evidence: EvalEvidence,
    chunks_by_id: dict[str, Chunk],
) -> list[AnswerProvenanceIssue]:
    if not evidence.chunk_id:
        return [_issue(case_id, evidence_index, "missing_chunk_id", "non-empty", None)]

    chunk = chunks_by_id.get(evidence.chunk_id)
    if chunk is None:
        return [
            _issue(
                case_id,
                evidence_index,
                "chunk_not_found",
                evidence.chunk_id,
                None,
            )
        ]

    issues: list[AnswerProvenanceIssue] = []
    if not evidence.quote:
        issues.append(_issue(case_id, evidence_index, "missing_quote", "non-empty", ""))
    elif _normalize_text(evidence.quote) not in _normalize_text(chunk.text):
        issues.append(
            _issue(case_id, evidence_index, "quote_mismatch", evidence.quote, chunk.text)
        )

    for field in ("page", "chapter", "section", "subsection"):
        expected = getattr(evidence, field)
        actual = getattr(chunk, field)
        if expected != actual:
            issues.append(
                _issue(
                    case_id,
                    evidence_index,
                    f"{field}_mismatch",
                    expected,
                    actual,
                )
            )

    actual_heading_path = _heading_path(chunk)
    if evidence.heading_path != actual_heading_path:
        issues.append(
            _issue(
                case_id,
                evidence_index,
                "heading_path_mismatch",
                evidence.heading_path,
                actual_heading_path,
            )
        )
    return issues


def _heading_path(chunk: Chunk) -> list[str]:
    value = chunk.metadata.get("heading_path")
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        return [part.strip() for part in value.split(">") if part.strip()]
    return [value for value in (chunk.chapter, chunk.section, chunk.subsection) if value]


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", "", text)


def _issue(
    case_id: str,
    evidence_index: int | None,
    issue_type: str,
    expected: Any,
    actual: Any,
) -> AnswerProvenanceIssue:
    return AnswerProvenanceIssue(
        case_id=case_id,
        evidence_index=evidence_index,
        issue_type=issue_type,
        expected=expected,
        actual=actual,
    )
