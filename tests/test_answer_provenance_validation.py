import json

import pytest

from app.data.schemas.models import Chunk
from app.evaluation.answer_evaluator import AnswerEvalCase, load_answer_eval_cases
from app.evaluation.answer_provenance_validation import (
    ensure_answer_eval_provenance_valid,
    validate_answer_eval_provenance,
)
from app.evaluation.schemas import EvalCase, EvalEvidence


def _chunk(chunk_id: str = "chunk-1") -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        doc_id="doc-1",
        source_file="manual.pdf",
        page=158,
        chapter="启动和驾驶",
        section="电子驻车制动（EPB）",
        subsection="EPB AUTO功能",
        text="EPB AUTO功能开启后，车辆静止并熄火时自动启用EPB。",
        metadata={
            "heading_path": ["启动和驾驶", "电子驻车制动（EPB）", "EPB AUTO功能"]
        },
    )


def _evidence(chunk_id: str = "chunk-1", **updates) -> EvalEvidence:
    payload = {
        "chunk_id": chunk_id,
        "page": 158,
        "chapter": "启动和驾驶",
        "section": "电子驻车制动（EPB）",
        "subsection": "EPB AUTO功能",
        "heading_path": ["启动和驾驶", "电子驻车制动（EPB）", "EPB AUTO功能"],
        "quote": "车辆静止并熄火时自动启用EPB。",
    }
    payload.update(updates)
    return EvalEvidence(**payload)


def _answer_case(**updates) -> AnswerEvalCase:
    payload = {
        "id": "answer-case",
        "question": "EPB AUTO功能开启后会怎样？",
        "answer_type": "condition",
        "source_case_id": "retrieval-case",
        "evidence": [_evidence().model_dump()],
    }
    payload.update(updates)
    return AnswerEvalCase(**payload)


def _retrieval_case(*evidence: EvalEvidence) -> EvalCase:
    return EvalCase(
        id="retrieval-case",
        question="EPB AUTO功能开启后会怎样？",
        category="explanation",
        intent_type="state_explanation",
        evidence=list(evidence or [_evidence()]),
    )


def test_answer_eval_loader_accepts_legal_jsonl_and_preserves_case_ids(tmp_path) -> None:
    dataset = tmp_path / "answer_eval.jsonl"
    cases = [_answer_case(id="case-a"), _answer_case(id="case-b")]
    dataset.write_text(
        "\n".join(json.dumps(case.model_dump(), ensure_ascii=False) for case in cases) + "\n",
        encoding="utf-8",
    )

    loaded = load_answer_eval_cases(dataset)

    assert [case.id for case in loaded] == ["case-a", "case-b"]


def test_answer_eval_loader_rejects_duplicate_case_ids(tmp_path) -> None:
    dataset = tmp_path / "answer_eval.jsonl"
    payload = json.dumps(_answer_case().model_dump(), ensure_ascii=False)
    dataset.write_text(f"{payload}\n{payload}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Duplicate answer eval case id"):
        load_answer_eval_cases(dataset)


def test_valid_answer_provenance_passes() -> None:
    result = ensure_answer_eval_provenance_valid(
        [_answer_case()],
        [_retrieval_case()],
        [_chunk()],
    )

    assert result.valid is True
    assert result.case_count == 1
    assert result.evidence_count == 1


def test_missing_source_case_fails() -> None:
    result = validate_answer_eval_provenance([_answer_case()], [], [_chunk()])

    assert result.issue_counts == {"source_case_not_found": 1}


def test_stale_chunk_id_fails() -> None:
    result = validate_answer_eval_provenance(
        [_answer_case(evidence=[_evidence("stale-id").model_dump()])],
        [_retrieval_case()],
        [_chunk()],
    )

    assert result.issue_counts == {"chunk_not_found": 1}


@pytest.mark.parametrize(
    ("field", "value", "issue_type"),
    [
        ("page", 999, "page_mismatch"),
        ("section", "旧章节", "section_mismatch"),
        ("subsection", "旧小节", "subsection_mismatch"),
        ("heading_path", ["旧路径"], "heading_path_mismatch"),
        ("quote", "不存在的旧文本", "quote_mismatch"),
    ],
)
def test_stale_evidence_fields_fail(field: str, value, issue_type: str) -> None:
    result = validate_answer_eval_provenance(
        [_answer_case(evidence=[_evidence(**{field: value}).model_dump()])],
        [_retrieval_case()],
        [_chunk()],
    )

    assert result.issue_counts == {issue_type: 1}


def test_hard_negative_passes_without_source_case_or_evidence() -> None:
    case = _answer_case(
        answer_type="insufficient_evidence",
        source_case_id=None,
        evidence=[],
        allow_insufficient_answer=True,
    )

    result = ensure_answer_eval_provenance_valid([case], [], [_chunk()])

    assert result.valid is True
    assert result.hard_negative_case_count == 1
    assert result.evidence_count == 0


def test_multi_gold_source_allows_one_canonical_answer_evidence() -> None:
    source_case = _retrieval_case(_evidence("chunk-1"), _evidence("chunk-2"))
    result = ensure_answer_eval_provenance_valid(
        [_answer_case(evidence=[_evidence("chunk-1").model_dump()])],
        [source_case],
        [_chunk("chunk-1"), _chunk("chunk-2")],
    )

    assert result.valid is True
    assert result.evidence_count == 1


def test_remote_start_contract_is_frozen_to_all_manual_supported_conditions() -> None:
    cases = load_answer_eval_cases("data/eval/answer_eval_set.jsonl")
    case = next(item for item in cases if item.id == "remote_start_blocked_answer_001")

    assert len(case.must_include_points) == 8
    assert {
        "冷却液液位较低",
        "燃油油位较低",
        "车内有遥控钥匙",
        "车门未锁定",
        "发动机故障",
    }.issubset(case.must_include_terms)
    assert "ANSWER_CONTRACT_REVIEW" not in case.notes
