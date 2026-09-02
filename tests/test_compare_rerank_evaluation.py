import json

import pytest

from scripts.compare_rerank_evaluation import (
    compare_reports,
    format_markdown_report,
    load_json_report,
)


def _case(
    case_id: str,
    *,
    rank: int | None,
    category: str = "procedure",
    intent_type: str = "specific_operation",
    top1_page: int = 10,
    top1_section: str | None = "示例章节",
    top5_hit: bool | None = None,
) -> dict:
    return {
        "case_id": case_id,
        "question": f"question-{case_id}",
        "category": category,
        "intent_type": intent_type,
        "retrieval_mode": "hybrid",
        "top_k": 5,
        "use_context_selection": False,
        "metrics": {
            "first_evidence_hit_rank": rank,
            "evidence_hit@1": rank == 1,
            "evidence_hit@3": rank is not None and rank <= 3,
            "evidence_hit@5": (rank is not None and rank <= 5) if top5_hit is None else top5_hit,
            "mrr": 1.0 / rank if rank else 0.0,
        },
        "raw_hits": [
            {
                "rank": 1,
                "chunk_id": f"chunk-{case_id}",
                "page": top1_page,
                "section": top1_section,
                "score": 0.5,
                "evidence_hit": rank == 1,
            }
        ],
        "final_hits": [],
        "failure_reasons": [],
    }


def _report(results: list[dict], *, rerank_enabled: bool, elapsed_seconds: float) -> dict:
    ranks = [item["metrics"]["first_evidence_hit_rank"] for item in results]
    return {
        "dataset_path": "data/eval/manual_eval_set.jsonl",
        "case_count": len(results),
        "retrieval_modes": ["hybrid"],
        "top_k": 5,
        "use_context_selection": False,
        "rerank_enabled": rerank_enabled,
        "rerank_model_name": "BAAI/bge-reranker-base" if rerank_enabled else None,
        "rerank_top_n": 10 if rerank_enabled else None,
        "rerank_output_top_k": 5 if rerank_enabled else None,
        "overall_metrics": {
            "evidence_hit@1": sum(rank == 1 for rank in ranks) / len(ranks),
            "evidence_hit@3": sum(rank is not None and rank <= 3 for rank in ranks) / len(ranks),
            "evidence_hit@5": sum(rank is not None and rank <= 5 for rank in ranks) / len(ranks),
            "mrr": sum(1.0 / rank if rank else 0.0 for rank in ranks) / len(ranks),
            "average_first_hit_rank": sum(rank for rank in ranks if rank) / sum(
                rank is not None for rank in ranks
            ),
        },
        "by_retrieval_mode": {},
        "by_category": {},
        "by_intent_type": {},
        "results": results,
        "generated_at": "2026-06-02T00:00:00",
        "elapsed_seconds": elapsed_seconds,
    }


def _comparison() -> dict:
    baseline = _report(
        [
            _case("improved", rank=3, top1_page=11, top1_section="弱相关章节"),
            _case("regressed", rank=1, top1_page=20, top1_section="正确章节"),
            _case("unchanged", rank=2, top1_page=30, top1_section=None),
            _case("top5-lost", rank=5, top1_page=40, top1_section="候选章节"),
        ],
        rerank_enabled=False,
        elapsed_seconds=10.0,
    )
    experiment = _report(
        [
            _case("improved", rank=1, top1_page=12, top1_section="正确章节"),
            _case("regressed", rank=3, top1_page=21, top1_section="错误章节"),
            _case("unchanged", rank=2, top1_page=30, top1_section=None),
            _case("top5-lost", rank=None, top1_page=41, top1_section="错误章节", top5_hit=False),
        ],
        rerank_enabled=True,
        elapsed_seconds=50.0,
    )
    return compare_reports(baseline, experiment)


def test_compare_reports_calculates_metric_delta_and_case_movements() -> None:
    comparison = _comparison()
    metric_rows = {item["metric"]: item for item in comparison["overall_metric_rows"]}

    assert metric_rows["evidence_hit@1"]["delta"] == pytest.approx(0.0)
    assert metric_rows["mrr"]["delta"] == pytest.approx(-0.05)
    assert comparison["movement_summary"] == {
        "improved_cases": 1,
        "regressed_cases": 2,
        "unchanged_cases": 1,
        "newly_top1_hit": 1,
        "lost_top1_hit": 1,
        "evidence_hit@5_regressions": 1,
    }
    assert [item["case_id"] for item in comparison["improved_cases"]] == ["improved"]
    assert {item["case_id"] for item in comparison["regressed_cases"]} == {
        "regressed",
        "top5-lost",
    }
    assert [item["case_id"] for item in comparison["unchanged_non_top1_cases"]] == [
        "unchanged"
    ]


def test_compare_reports_renders_optional_values_as_na() -> None:
    comparison = _comparison()
    markdown = format_markdown_report(comparison)

    assert "# Rerank Evaluation Comparison" in markdown
    assert "V3.1.2 Rerank Evaluation Comparison" not in markdown
    assert "## 6. Regressed Cases" in markdown
    assert "| unchanged | procedure | specific_operation | 2 | 2 | N/A | N/A |" in markdown
    assert "| final_context_hit | N/A | N/A | N/A |" in markdown
    assert "| elapsed_seconds | 10.0000 | 50.0000 | +40.0000 | 5.00x |" in markdown


def test_compare_reports_supports_custom_markdown_title() -> None:
    markdown = format_markdown_report(
        _comparison(),
        report_title="V3.4 Rerank Evaluation Comparison",
    )

    assert markdown.startswith("# V3.4 Rerank Evaluation Comparison\n")


def test_compare_reports_rejects_mismatched_case_ids() -> None:
    baseline = _report([_case("baseline-only", rank=1)], rerank_enabled=False, elapsed_seconds=1.0)
    experiment = _report(
        [_case("experiment-only", rank=1)],
        rerank_enabled=True,
        elapsed_seconds=2.0,
    )

    with pytest.raises(ValueError, match="missing_in_experiment"):
        compare_reports(baseline, experiment)


def test_compare_reports_rejects_mismatched_case_count() -> None:
    baseline = _report([_case("case-1", rank=1)], rerank_enabled=False, elapsed_seconds=1.0)
    experiment = _report([_case("case-1", rank=1)], rerank_enabled=True, elapsed_seconds=2.0)
    experiment["case_count"] = 2

    with pytest.raises(ValueError, match="case counts do not match"):
        compare_reports(baseline, experiment)


def test_load_json_report_reads_structured_report(tmp_path) -> None:
    path = tmp_path / "report.json"
    payload = _report([_case("case-1", rank=1)], rerank_enabled=False, elapsed_seconds=1.0)
    path.write_text(json.dumps(payload), encoding="utf-8")

    assert load_json_report(path) == payload
