import re
from collections import Counter
from typing import Any

from pydantic import BaseModel, Field

from app.data.schemas.models import Chunk
from app.evaluation.schemas import EvalCase, EvalEvidence


class BenchmarkValidationIssue(BaseModel):
    case_id: str
    evidence_index: int
    issue_type: str
    expected: Any = None
    actual: Any = None


class BenchmarkValidationResult(BaseModel):
    case_count: int
    excluded_case_count: int = 0
    evidence_count: int
    valid: bool
    issue_counts: dict[str, int] = Field(default_factory=dict)
    issues: list[BenchmarkValidationIssue] = Field(default_factory=list)


def validate_retrieval_benchmark(
    cases: list[EvalCase],
    chunks: list[Chunk],
) -> BenchmarkValidationResult:
    chunks_by_id = {chunk.chunk_id: chunk for chunk in chunks}
    issues: list[BenchmarkValidationIssue] = []
    evidence_count = 0
    active_case_count = 0
    excluded_case_count = 0
    for case in cases:
        if case.excluded:
            excluded_case_count += 1
            continue
        active_case_count += 1
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
    return BenchmarkValidationResult(
        case_count=active_case_count,
        excluded_case_count=excluded_case_count,
        evidence_count=evidence_count,
        valid=not issues,
        issue_counts=dict(counts),
        issues=issues,
    )


def format_validation_failure(result: BenchmarkValidationResult, limit: int = 20) -> str:
    details = "; ".join(
        f"case={issue.case_id} evidence={issue.evidence_index} "
        f"type={issue.issue_type} expected={issue.expected!r} actual={issue.actual!r}"
        for issue in result.issues[:limit]
    )
    suffix = "" if len(result.issues) <= limit else f"; ... {len(result.issues) - limit} more"
    return (
        "Retrieval benchmark is inconsistent with the current index: "
        f"issues={len(result.issues)} counts={result.issue_counts}. {details}{suffix}"
    )


def ensure_retrieval_benchmark_valid(
    cases: list[EvalCase],
    chunks: list[Chunk],
) -> BenchmarkValidationResult:
    result = validate_retrieval_benchmark(cases, chunks)
    if not result.valid:
        raise ValueError(format_validation_failure(result))
    return result


def _validate_evidence(
    case_id: str,
    evidence_index: int,
    evidence: EvalEvidence,
    chunks_by_id: dict[str, Chunk],
) -> list[BenchmarkValidationIssue]:
    if not evidence.chunk_id:
        return [
            _issue(case_id, evidence_index, "missing_gold_chunk_id", "non-empty", None)
        ]
    chunk = chunks_by_id.get(evidence.chunk_id)
    if chunk is None:
        return [
            _issue(
                case_id,
                evidence_index,
                "gold_chunk_not_found",
                evidence.chunk_id,
                None,
            )
        ]

    issues: list[BenchmarkValidationIssue] = []
    if evidence.quote and _normalize_text(evidence.quote) not in _normalize_text(chunk.text):
        issues.append(
            _issue(case_id, evidence_index, "gold_text_mismatch", evidence.quote, chunk.text)
        )
    for field in ("page", "chapter", "section", "subsection"):
        expected = getattr(evidence, field)
        if expected is None or expected == "":
            continue
        actual = getattr(chunk, field)
        if expected != actual:
            issues.append(
                _issue(
                    case_id,
                    evidence_index,
                    f"gold_{field}_mismatch",
                    expected,
                    actual,
                )
            )
    if evidence.heading_path:
        actual_path = _heading_path(chunk)
        if evidence.heading_path != actual_path:
            issues.append(
                _issue(
                    case_id,
                    evidence_index,
                    "gold_heading_path_mismatch",
                    evidence.heading_path,
                    actual_path,
                )
            )
    return issues


def _heading_path(chunk: Chunk) -> list[str]:
    value = chunk.metadata.get("heading_path")
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        return [part.strip() for part in value.split(">") if part.strip()]
    return [item for item in (chunk.chapter, chunk.section, chunk.subsection) if item]


def _issue(
    case_id: str,
    evidence_index: int,
    issue_type: str,
    expected: Any,
    actual: Any,
) -> BenchmarkValidationIssue:
    return BenchmarkValidationIssue(
        case_id=case_id,
        evidence_index=evidence_index,
        issue_type=issue_type,
        expected=expected,
        actual=actual,
    )


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", "", text)
