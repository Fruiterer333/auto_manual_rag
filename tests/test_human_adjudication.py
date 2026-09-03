from app.evaluation.answer_evaluator import (
    AnswerCitationRecord,
    AnswerCaseResult,
    AnswerEvaluationRun,
    AnswerPromptEvidenceRecord,
    DeterministicAnswerChecks,
)
from app.evaluation.human_adjudication import (
    HumanAdjudicationRecord,
    HumanAdjudicationSource,
    build_human_adjudicated_run,
    load_human_adjudication_source,
    summarize_human_adjudications,
)


def _result(case_id: str) -> AnswerCaseResult:
    return AnswerCaseResult(
        case_id=case_id,
        question=f"问题 {case_id}",
        answer_type="explanation",
        final_answer="冻结答案",
        retrieval_mode="hybrid",
        deterministic_checks=DeterministicAnswerChecks(answer_non_empty=True),
        elapsed_seconds=0.1,
    )


def _review(
    case_id: str,
    *,
    score: int = 2,
    diagnostic: bool = False,
) -> HumanAdjudicationRecord:
    return HumanAdjudicationRecord(
        case_id=case_id,
        groundedness=score,
        correctness=score,
        completeness=score,
        condition_handling=score,
        safety_preservation=score,
        unsupported_claim=False,
        critical_safety_omission=False,
        primary_failure_layer="NONE",
        evaluator_diagnostics=["EVALUATOR_PROXY_FALSE_NEGATIVE"] if diagnostic else [],
        rationale="人工裁决理由",
        adjudication_status="final",
    )


def test_build_adjudicated_run_preserves_frozen_answer_fields() -> None:
    first = _result("case-1")
    first.raw_answer = "原始答案"
    first.prompt_evidence = [
        AnswerPromptEvidenceRecord(
            evidence_id="E1",
            order=1,
            chunk_id="chunk-1",
            page=99,
            heading_path="章节 > 小节",
            text="冻结 Evidence",
            content_type="normal",
            truncated=False,
            original_text_chars=6,
            prompt_text_chars=6,
        )
    ]
    first.citations = [
        AnswerCitationRecord(page=99, chunk_id="chunk-1", quote="冻结引用")
    ]
    baseline = AnswerEvaluationRun(
        generated_at="2026-09-02T20:03:02",
        dataset_path="data/eval/answer_eval_set.jsonl",
        case_count=2,
        semantics_version="v4.3",
        config={"retrieval_mode": "hybrid"},
        summary={"answer_non_empty_pass": 2},
        results=[first, _result("case-2")],
    )
    source = HumanAdjudicationSource(
        adjudication_version="v4.5-b-final",
        source_baseline_path="reports/evaluation/baseline.json",
        records=[_review("case-1"), _review("case-2", diagnostic=True)],
    )

    adjudicated = build_human_adjudicated_run(
        baseline,
        source_baseline_path=source.source_baseline_path,
        adjudication_source=source,
    )

    assert adjudicated.case_count == 2
    assert adjudicated.results[0].raw_answer == "原始答案"
    assert adjudicated.results[0].final_answer == "冻结答案"
    assert adjudicated.results[0].prompt_evidence == first.prompt_evidence
    assert adjudicated.results[0].citations == first.citations
    assert adjudicated.results[0].deterministic_checks.answer_non_empty is True
    assert adjudicated.results[0].human_review.groundedness == 2
    assert adjudicated.results[1].human_adjudication.adjudication_status == "final"


def test_human_full_pass_is_not_changed_by_evaluator_diagnostic() -> None:
    baseline = AnswerEvaluationRun(
        generated_at="2026-09-02T20:03:02",
        dataset_path="data/eval/answer_eval_set.jsonl",
        case_count=2,
        results=[_result("case-1"), _result("case-2")],
    )
    source = HumanAdjudicationSource(
        adjudication_version="v4.5-b-final",
        source_baseline_path="reports/evaluation/baseline.json",
        records=[_review("case-1", diagnostic=True), _review("case-2", score=0)],
    )
    adjudicated = build_human_adjudicated_run(
        baseline,
        source_baseline_path=source.source_baseline_path,
        adjudication_source=source,
    )

    summary = summarize_human_adjudications(adjudicated.results)

    assert summary["human_full_pass_count"] == 1
    assert summary["human_full_pass_rate"] == 0.5
    assert summary["severe_failure_count"] == 1
    assert summary["evaluator_diagnostic_frequency"] == {
        "EVALUATOR_PROXY_FALSE_NEGATIVE": 1
    }


def test_adjudication_requires_one_final_record_for_each_baseline_case() -> None:
    baseline = AnswerEvaluationRun(
        generated_at="2026-09-02T20:03:02",
        dataset_path="data/eval/answer_eval_set.jsonl",
        case_count=2,
        results=[_result("case-1"), _result("case-2")],
    )
    source = HumanAdjudicationSource(
        adjudication_version="v4.5-b-final",
        source_baseline_path="reports/evaluation/baseline.json",
        records=[_review("case-1")],
    )

    try:
        build_human_adjudicated_run(
            baseline,
            source_baseline_path=source.source_baseline_path,
            adjudication_source=source,
        )
    except ValueError as error:
        assert "missing=['case-2']" in str(error)
    else:
        raise AssertionError("Expected baseline/adjudication mismatch to fail")


def test_final_human_adjudication_source_contains_twelve_final_records() -> None:
    source = load_human_adjudication_source("data/eval/v4_5_b_human_adjudication.json")

    assert source.adjudication_version == "v4.5-b-final"
    assert len(source.records) == 12
    assert {record.adjudication_status for record in source.records} == {"final"}
    for record in source.records:
        assert all(
            getattr(record, field) in {0, 1, 2}
            for field in (
                "groundedness",
                "correctness",
                "completeness",
                "condition_handling",
                "safety_preservation",
            )
        )
