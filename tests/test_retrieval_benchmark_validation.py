import pytest

from app.data.schemas.models import Chunk, RetrievedChunk
from app.evaluation.benchmark_validation import (
    ensure_retrieval_benchmark_valid,
    validate_retrieval_benchmark,
)
from app.evaluation.metrics import evaluate_case_retrieval
from app.evaluation.schemas import EvalCase, EvalEvidence


def _chunk(
    chunk_id: str,
    *,
    text: str = "EPB AUTO功能开启后，车辆熄火时自动启用EPB。",
    section: str = "电子驻车制动（EPB）",
    subsection: str = "EPB AUTO功能",
) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        doc_id=f"doc-{chunk_id}",
        source_file="manual.pdf",
        page=158,
        chapter="启动和驾驶",
        section=section,
        subsection=subsection,
        text=text,
        metadata={
            "heading_path": ["启动和驾驶", section, subsection],
        },
    )


def _case(*evidence: EvalEvidence) -> EvalCase:
    return EvalCase(
        id="epb-case",
        question="EPB AUTO功能是什么？",
        category="explanation",
        intent_type="state_explanation",
        evidence=list(evidence),
    )


def _evidence(chunk_id: str, **updates) -> EvalEvidence:
    payload = {
        "chunk_id": chunk_id,
        "page": 158,
        "chapter": "启动和驾驶",
        "section": "电子驻车制动（EPB）",
        "subsection": "EPB AUTO功能",
        "heading_path": ["启动和驾驶", "电子驻车制动（EPB）", "EPB AUTO功能"],
        "quote": "EPB AUTO功能开启后，车辆熄火时自动启用EPB。",
    }
    payload.update(updates)
    return EvalEvidence(**payload)


def test_benchmark_validation_passes_for_matching_gold_chunk() -> None:
    result = validate_retrieval_benchmark(
        [_case(_evidence("gold-1"))],
        [_chunk("gold-1")],
    )

    assert result.valid is True
    assert result.issues == []


def test_benchmark_validation_fails_when_gold_chunk_is_missing() -> None:
    result = validate_retrieval_benchmark(
        [_case(_evidence("stale-id"))],
        [_chunk("gold-1")],
    )

    assert result.valid is False
    assert result.issue_counts == {"gold_chunk_not_found": 1}


def test_stale_benchmark_fails_fast_instead_of_becoming_retrieval_miss() -> None:
    with pytest.raises(ValueError, match="gold_chunk_not_found"):
        ensure_retrieval_benchmark_valid(
            [_case(_evidence("stale-id"))],
            [_chunk("gold-1")],
        )


def test_excluded_case_does_not_require_a_current_gold_chunk() -> None:
    excluded_case = _case(_evidence("stale-id"))
    excluded_case.excluded = True
    excluded_case.exclusion_reason = "Required evidence is absent from the corpus."

    result = ensure_retrieval_benchmark_valid([excluded_case], [_chunk("gold-1")])

    assert result.valid is True
    assert result.case_count == 0
    assert result.excluded_case_count == 1
    assert result.evidence_count == 0


def test_benchmark_validation_detects_text_mismatch() -> None:
    result = validate_retrieval_benchmark(
        [_case(_evidence("gold-1", quote="不存在的旧文本"))],
        [_chunk("gold-1")],
    )

    assert result.issue_counts == {"gold_text_mismatch": 1}


def test_benchmark_validation_detects_section_and_subsection_mismatch() -> None:
    result = validate_retrieval_benchmark(
        [
            _case(
                _evidence(
                    "gold-1",
                    section="旧章节",
                    subsection="旧小节",
                    heading_path=[],
                )
            )
        ],
        [_chunk("gold-1")],
    )

    assert result.issue_counts == {
        "gold_section_mismatch": 1,
        "gold_subsection_mismatch": 1,
    }


def test_multiple_gold_chunks_hit_when_any_gold_is_retrieved() -> None:
    case = _case(_evidence("gold-a"), _evidence("gold-b"))
    retrieved = [
        RetrievedChunk(chunk=_chunk("wrong"), score=0.9),
        RetrievedChunk(chunk=_chunk("gold-b"), score=0.8),
    ]

    result = evaluate_case_retrieval(
        case,
        retrieved,
        retrieval_mode="hybrid",
        top_k=5,
    )

    assert result.metrics["evidence_hit@1"] is False
    assert result.metrics["evidence_hit@3"] is True
    assert result.metrics["evidence_hit@5"] is True
    assert result.metrics["first_evidence_hit_rank"] == 2
    assert result.metrics["mrr"] == 0.5
