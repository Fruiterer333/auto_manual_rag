import json

import pytest
from pydantic import ValidationError

from app.data.schemas.models import Citation, QueryResponse
from app.evaluation.answer_evaluator import (
    ANSWER_EVAL_SEMANTICS_VERSION,
    AnswerEvalCase,
    AnswerCaseResult,
    HumanAnswerReview,
    build_answer_evaluation_run,
    evaluate_answer_response,
    ensure_answer_eval_semantics_valid,
    has_internal_reference_leak,
    load_answer_eval_cases,
    render_answer_evaluation_markdown,
    validate_answer_eval_semantics,
)
from app.rag.prompts.answer_prompt import PromptEvidenceSnapshot


def _case(**updates) -> AnswerEvalCase:
    payload = {
        "id": "case-1",
        "question": "如何操作？",
        "answer_type": "procedure",
        "must_include_terms": ["电子驻车制动", "制动踏板"],
        "must_include_points": ["说明操作条件"],
        "must_not_include_terms": ["无需制动"],
        "must_not_claim": ["不得编造自动操作"],
        "critical_warning_points": [],
        "expected_sections": ["电子驻车制动（EPB）"],
        "expected_subsections": ["释放电子驻车制动（EPB）"],
        "allow_insufficient_answer": False,
    }
    payload.update(updates)
    return AnswerEvalCase(**payload)


def _response(answer: str) -> QueryResponse:
    return QueryResponse(
        question="如何操作？",
        answer=answer,
        retrieval_mode="hybrid",
        citations=[
            Citation(
                source_file="manual.pdf",
                page=158,
                chapter="启动和驾驶",
                section="电子驻车制动（EPB）",
                subsection="释放电子驻车制动（EPB）",
                chunk_id="chunk-1",
                quote="踩下制动踏板并按下EPB开关。",
            )
        ],
    )


def test_answer_eval_dataset_case_parses_with_empty_optional_fields(tmp_path) -> None:
    dataset = tmp_path / "answer_eval.jsonl"
    dataset.write_text(
        json.dumps(
            {
                "id": "minimal",
                "question": "手册中有依据吗？",
                "answer_type": "insufficient_evidence",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    cases = load_answer_eval_cases(dataset)

    assert len(cases) == 1
    assert cases[0].must_include_terms == []
    assert cases[0].expected_sections == []
    assert cases[0].evidence == []


def test_must_include_term_coverage_and_forbidden_terms() -> None:
    result = evaluate_answer_response(
        _case(),
        _response("操作电子驻车制动时无需制动。"),
        elapsed_seconds=0.25,
        retrieval_mode="hybrid",
    )

    assert result.deterministic_checks.must_include_term_coverage == 0.5
    assert result.deterministic_checks.matched_must_include_terms == ["电子驻车制动"]
    assert result.deterministic_checks.missing_must_include_terms == ["制动踏板"]
    assert result.deterministic_checks.forbidden_term_hits == ["无需制动"]


def test_term_coverage_uses_normalization_but_preserves_original_terms() -> None:
    result = evaluate_answer_response(
        _case(must_include_terms=["10 cm", "ABS"]),
        _response("与传感器保持10厘米距离，abs功能保持正常。"),
        elapsed_seconds=0.1,
        retrieval_mode="hybrid",
    )

    assert result.deterministic_checks.matched_must_include_terms == ["10 cm", "ABS"]
    assert result.deterministic_checks.missing_must_include_terms == []
    assert result.deterministic_checks.must_include_term_coverage == 1.0


@pytest.mark.parametrize(
    "answer",
    [
        "Evidence E1",
        "[EVIDENCE E1]",
        "E1 Evidence",
        "E3证据",
        "E5 证据",
        "证据 E2",
        "参照E3证据",
        "参考 E2 证据",
        "根据Evidence E4",
        "根据 Evidence E5",
        "参考[EVIDENCE E2]",
    ],
)
def test_internal_reference_detection_recognizes_explicit_markers(answer: str) -> None:
    assert has_internal_reference_leak(answer) is True


@pytest.mark.parametrize(
    "answer",
    [
        "E1",
        "故障代码 E1 表示传感器异常。",
        "显示屏提示 E2。",
        "车辆采用 E1 级材料。",
        "根据车辆状态进行操作。",
        "具体要求请参考用户手册。",
        "参见保养章节。",
    ],
)
def test_internal_reference_detection_preserves_non_internal_text(answer: str) -> None:
    assert has_internal_reference_leak(answer) is False


def test_expected_section_and_subsection_hit() -> None:
    result = evaluate_answer_response(
        _case(),
        _response("踩下制动踏板，操作电子驻车制动。"),
        elapsed_seconds=0.1,
        retrieval_mode="hybrid",
    )

    checks = result.deterministic_checks
    assert checks.expected_section_hit is True
    assert checks.expected_subsection_hit is True
    assert checks.evidence_structure_hit is True
    assert result.citations[0].subsection == "释放电子驻车制动（EPB）"


def test_insufficient_evidence_behavior_uses_standard_fallback() -> None:
    result = evaluate_answer_response(
        _case(
            answer_type="insufficient_evidence",
            allow_insufficient_answer=True,
            expected_sections=[],
            expected_subsections=[],
        ),
        QueryResponse(
            question="未知问题",
            answer="我没有在手册中找到可靠依据",
            citations=[],
        ),
        elapsed_seconds=0.1,
        retrieval_mode="hybrid",
    )

    assert result.deterministic_checks.insufficient_evidence_behavior is True
    assert result.deterministic_checks.evidence_structure_hit is None


def test_human_review_defaults_to_not_scored() -> None:
    result = evaluate_answer_response(
        _case(),
        _response("踩下制动踏板，操作电子驻车制动。"),
        elapsed_seconds=0.1,
        retrieval_mode="hybrid",
    )

    assert result.human_review.groundedness is None
    assert result.human_review.correctness is None
    assert result.human_review.unsupported_claim is None
    assert result.human_review.critical_safety_omission is None


@pytest.mark.parametrize("score", [0, 1, 2])
def test_human_review_accepts_frozen_score_range(score: int) -> None:
    review = HumanAnswerReview(
        groundedness=score,
        correctness=score,
        completeness=score,
        condition_handling=score,
        safety_preservation=score,
    )

    assert review.groundedness == score


@pytest.mark.parametrize("score", [-1, 3])
def test_human_review_rejects_scores_outside_frozen_range(score: int) -> None:
    with pytest.raises(ValidationError):
        HumanAnswerReview(groundedness=score)


def test_semantics_validation_rejects_outstanding_contract_review() -> None:
    result = validate_answer_eval_semantics(
        [_case(notes="ANSWER_CONTRACT_REVIEW: unresolved")]
    )

    assert result.valid is False
    assert result.outstanding_contract_reviews == ["case-1"]


def test_semantics_validation_passes_frozen_contracts() -> None:
    result = ensure_answer_eval_semantics_valid([_case(notes="contract frozen")])

    assert result.valid is True
    assert result.semantics_version == "v4.3"
    assert result.rubric_schema_valid is True


def test_markdown_report_contains_auditable_sections_and_todos() -> None:
    result = evaluate_answer_response(
        _case(),
        _response("踩下制动踏板，操作电子驻车制动。"),
        elapsed_seconds=0.1,
        retrieval_mode="hybrid",
    )
    run = build_answer_evaluation_run(
        dataset_path="data/eval/answer_eval_set.jsonl",
        config={"retrieval_mode": "hybrid", "llm_model": "test-model"},
        results=[result],
    )

    markdown = render_answer_evaluation_markdown(run)

    assert "# Answer Generation Evaluation" in markdown
    assert "Human semantic review has not been completed." in markdown
    assert "## Case Details" in markdown
    assert "**Raw answer:**" in markdown
    assert "**Final answer:**" in markdown
    assert "**Prompt Evidence:**" in markdown
    assert "subsection=释放电子驻车制动（EPB）" in markdown
    assert "Groundedness: TODO / NOT REVIEWED" in markdown
    assert "Safety Preservation: N/A" in markdown
    assert "Critical safety omission: TODO / NOT REVIEWED" in markdown
    assert run.summary["answer_non_empty_pass"] == 1
    assert run.semantics_version == ANSWER_EVAL_SEMANTICS_VERSION
    assert "semantics_version: v4.3" in markdown


def test_answer_result_serializes_raw_final_and_prompt_evidence() -> None:
    snapshot = PromptEvidenceSnapshot(
        evidence_id="E1",
        order=1,
        chunk_id="chunk-1",
        page=158,
        chapter="启动和驾驶",
        section="电子驻车制动（EPB）",
        subsection="释放电子驻车制动（EPB）",
        heading_path="启动和驾驶 > 电子驻车制动（EPB） > 释放电子驻车制动（EPB）",
        content_type="procedure",
        text="踩下制动踏板并按下EPB开关。",
        truncated=False,
        original_text_chars=16,
        prompt_text_chars=16,
    )
    result = evaluate_answer_response(
        _case(source_case_id="retrieval-case-1"),
        _response("踩下制动踏板，操作电子驻车制动。"),
        elapsed_seconds=0.1,
        retrieval_mode="hybrid",
        raw_answer="根据 Evidence E1，踩下制动踏板，操作电子驻车制动。",
        prompt_evidence=[snapshot],
    )

    reloaded = AnswerCaseResult.model_validate_json(result.model_dump_json())

    assert reloaded.source_case_id == "retrieval-case-1"
    assert reloaded.raw_answer.startswith("根据 Evidence E1")
    assert reloaded.final_answer == "踩下制动踏板，操作电子驻车制动。"
    assert reloaded.prompt_evidence[0].model_dump() == snapshot.__dict__


def test_legacy_answer_result_loads_answer_as_final_answer() -> None:
    legacy = {
        "case_id": "legacy-case",
        "question": "如何操作？",
        "answer_type": "procedure",
        "answer": "旧版最终答案",
        "retrieval_mode": "hybrid",
        "deterministic_checks": {"answer_non_empty": True},
        "elapsed_seconds": 0.1,
    }

    result = AnswerCaseResult.model_validate(legacy)

    assert result.final_answer == "旧版最终答案"
    assert result.raw_answer is None
    assert result.prompt_evidence == []
