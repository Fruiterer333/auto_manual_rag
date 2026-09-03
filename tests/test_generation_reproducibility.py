from app.evaluation.answer_evaluator import AnswerEvalCase
from app.rag.chains.qa_chain import AnswerGenerationTrace
from app.data.schemas.models import QueryResponse
from app.rag.prompts.answer_prompt import PromptEvidenceSnapshot
from scripts.verify_generation_reproducibility import (
    build_verification_artifact,
    select_stability_cases,
    summarize_case_runs,
    trace_record,
)


def _case(case_id: str) -> AnswerEvalCase:
    return AnswerEvalCase(
        id=case_id,
        question="测试问题",
        answer_type="explanation",
    )


def _trace(
    raw_answer: str,
    final_answer: str,
    chunk_id: str = "chunk-1",
    evidence_text: str = "证据正文",
) -> AnswerGenerationTrace:
    evidence = PromptEvidenceSnapshot(
        evidence_id="E1",
        order=1,
        chunk_id=chunk_id,
        page=1,
        chapter=None,
        section=None,
        subsection=None,
        heading_path="N/A",
        content_type="normal",
        text=evidence_text,
        truncated=False,
        original_text_chars=4,
        prompt_text_chars=4,
    )
    return AnswerGenerationTrace(
        response=QueryResponse(question="测试问题", answer=final_answer, citations=[]),
        raw_answer=raw_answer,
        final_answer=final_answer,
        prompt_evidence=(evidence,),
    )


def test_select_stability_cases_keeps_requested_order() -> None:
    cases = [_case("case-2"), _case("case-1")]

    selected = select_stability_cases(cases, ("case-1", "case-2"))

    assert [case.id for case in selected] == ["case-1", "case-2"]


def test_stability_summary_requires_raw_final_and_evidence_identity_matches() -> None:
    case = _case("case-1")
    stable = summarize_case_runs(
        case=case,
        runs=[
            trace_record(1, _trace("原始答案", "最终答案")),
            trace_record(2, _trace("原始答案", "最终答案")),
            trace_record(3, _trace("原始答案", "最终答案")),
        ],
    )
    changed_raw = summarize_case_runs(
        case=case,
        runs=[
            trace_record(1, _trace("原始答案", "最终答案")),
            trace_record(2, _trace("不同原始答案", "最终答案")),
            trace_record(3, _trace("原始答案", "最终答案")),
        ],
    )
    changed_evidence_text = summarize_case_runs(
        case=case,
        runs=[
            trace_record(1, _trace("原始答案", "最终答案")),
            trace_record(2, _trace("原始答案", "最终答案", evidence_text="不同证据")),
            trace_record(3, _trace("原始答案", "最终答案")),
        ],
    )

    assert stable["case_stable"] is True
    assert changed_raw["raw_answer_exact_match"] is False
    assert changed_raw["final_answer_exact_match"] is True
    assert changed_raw["case_stable"] is False
    assert changed_evidence_text["prompt_evidence_identity_exact_match"] is False
    assert changed_evidence_text["prompt_evidence_identity_order_text_exact_match"] is False
    assert changed_evidence_text["case_stable"] is False


def test_environment_blocked_artifact_is_not_reported_as_verified() -> None:
    artifact = build_verification_artifact(
        status="ENVIRONMENT_BLOCKED",
        settings_metadata={"generation_temperature": 0.0, "generation_seed": 42},
        runtime_metadata={"ollama_version": None},
        cases=[],
        runs_per_case=3,
        environment_error="runtime unavailable",
    )

    assert artifact["repeated_run_stability_verified"] is False
    assert artifact["raw_answer_exact_match_all_cases"] is False
