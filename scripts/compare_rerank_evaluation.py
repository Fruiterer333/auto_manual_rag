import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


CORE_METRICS = (
    "evidence_hit@1",
    "evidence_hit@3",
    "evidence_hit@5",
    "mrr",
    "average_first_hit_rank",
    "page_hit@1",
    "term_coverage_ratio@1",
    "final_context_hit",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare no-rerank and rerank retrieval evaluation JSON reports."
    )
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--output")
    parser.add_argument("--output-format", choices=("md", "json"), default="md")
    parser.add_argument(
        "--report-title",
        default="Rerank Evaluation Comparison",
        help="Markdown report title. Defaults to a version-neutral title.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    comparison = compare_reports(
        load_json_report(Path(args.baseline)),
        load_json_report(Path(args.experiment)),
        baseline_path=args.baseline,
        experiment_path=args.experiment,
    )
    output_text = (
        format_markdown_report(comparison, report_title=args.report_title)
        if args.output_format == "md"
        else json.dumps(comparison, ensure_ascii=False, indent=2)
    )
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output_text, encoding="utf-8")
        print(output_text)
        print(f"\nreport_output={output_path}")
    else:
        print(output_text)


def load_json_report(path: Path) -> dict[str, Any]:
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Evaluation JSON report not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid evaluation JSON report: {path}: {exc}") from exc
    if not isinstance(report, dict):
        raise ValueError(f"Evaluation JSON report must be an object: {path}")
    return report


def compare_reports(
    baseline: dict[str, Any],
    experiment: dict[str, Any],
    *,
    baseline_path: str = "baseline",
    experiment_path: str = "experiment",
) -> dict[str, Any]:
    baseline_results = _index_results(baseline, report_name="baseline")
    experiment_results = _index_results(experiment, report_name="experiment")
    baseline_ids = set(baseline_results)
    experiment_ids = set(experiment_results)
    if baseline_ids != experiment_ids:
        raise ValueError(
            "Evaluation case ids do not match: "
            f"missing_in_experiment={sorted(baseline_ids - experiment_ids)} "
            f"missing_in_baseline={sorted(experiment_ids - baseline_ids)}"
        )
    baseline_count = _case_count(baseline)
    experiment_count = _case_count(experiment)
    if baseline_count != experiment_count or baseline_count != len(baseline_ids):
        raise ValueError(
            "Evaluation case counts do not match: "
            f"baseline={baseline_count} experiment={experiment_count} "
            f"comparable_cases={len(baseline_ids)}"
        )

    movements = [
        _compare_case(baseline_results[case_id], experiment_results[case_id])
        for case_id in sorted(baseline_ids)
    ]
    improved = sorted(
        [row for row in movements if row["movement"] == "improved"],
        key=_improved_sort_key,
    )
    regressed = sorted(
        [row for row in movements if row["movement"] == "regressed"],
        key=_regressed_sort_key,
    )
    unchanged_non_top1 = [
        row
        for row in movements
        if row["movement"] == "unchanged" and row["experiment_rank"] != 1
    ]
    overall_rows = _overall_metric_rows(baseline, experiment)
    summary = {
        "improved_cases": len(improved),
        "regressed_cases": len(regressed),
        "unchanged_cases": sum(row["movement"] == "unchanged" for row in movements),
        "newly_top1_hit": sum(bool(row["newly_top1_hit"]) for row in movements),
        "lost_top1_hit": sum(bool(row["lost_top1_hit"]) for row in movements),
        "evidence_hit@5_regressions": sum(
            bool(row["evidence_hit@5_regression"]) for row in movements
        ),
    }
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "baseline_path": baseline_path,
        "experiment_path": experiment_path,
        "run_metadata": {
            "retrieval_mode": (
                _single_retrieval_mode(baseline),
                _single_retrieval_mode(experiment),
            ),
            "rerank_enabled": (
                baseline.get("rerank_enabled"),
                experiment.get("rerank_enabled"),
            ),
            "rerank_model_name": (
                baseline.get("rerank_model_name"),
                experiment.get("rerank_model_name"),
            ),
            "top_k": (baseline.get("top_k"), experiment.get("top_k")),
            "case_count": (baseline_count, experiment_count),
            "elapsed_seconds": (
                baseline.get("elapsed_seconds"),
                experiment.get("elapsed_seconds"),
            ),
        },
        "overall_metric_rows": overall_rows,
        "decision_summary": _decision_summary(overall_rows),
        "movement_summary": summary,
        "improved_cases": improved,
        "regressed_cases": regressed,
        "unchanged_non_top1_cases": unchanged_non_top1,
        "category_delta": _group_delta_rows(
            baseline_results.values(),
            experiment_results.values(),
            group_field="category",
        ),
        "intent_type_delta": _group_delta_rows(
            baseline_results.values(),
            experiment_results.values(),
            group_field="intent_type",
        ),
        "latency": _latency_summary(baseline, experiment, baseline_count),
        "recommendation": _recommendation(overall_rows, summary),
    }


def format_markdown_report(
    comparison: dict[str, Any],
    *,
    report_title: str = "Rerank Evaluation Comparison",
) -> str:
    lines = [
        f"# {report_title}",
        "",
        f"- generated_at: {comparison['generated_at']}",
        f"- baseline: `{comparison['baseline_path']}`",
        f"- experiment: `{comparison['experiment_path']}`",
        "",
        "## 1. Run Metadata",
        "",
        _metadata_table(comparison["run_metadata"]),
        "",
        "## 2. Overall Metric Delta",
        "",
        _metric_delta_table(comparison["overall_metric_rows"]),
        "",
        "Delta interpretation: larger is better for evidence hit, MRR, page hit, and term coverage. "
        "Smaller is better for average first hit rank. Larger elapsed time means higher cost.",
        "",
        "## 3. Decision Summary",
        "",
        comparison["decision_summary"],
        "",
        "## 4. Case Movement Summary",
        "",
        _movement_summary_table(comparison["movement_summary"]),
        "",
        "## 5. Improved Cases",
        "",
        _case_movement_table(comparison["improved_cases"], empty_message="No improved cases found."),
        "",
        "## 6. Regressed Cases",
        "",
        _case_movement_table(comparison["regressed_cases"], empty_message="No regressed cases found."),
        "",
        "## 7. Unchanged Non-Top1 Cases",
        "",
        _unchanged_case_table(comparison["unchanged_non_top1_cases"]),
        "",
        "## 8. Category Delta",
        "",
        _group_delta_table(comparison["category_delta"], group_label="category"),
        "",
        "Categories with very small case counts should be treated as directional signals only.",
        "",
        "## 9. Intent Type Delta",
        "",
        _group_delta_table(comparison["intent_type_delta"], group_label="intent_type"),
        "",
        "Intent types with very small case counts should be treated as directional signals only.",
        "",
        "## 10. Latency and Cost",
        "",
        _latency_table(comparison["latency"]),
        "",
        "Rerank may improve ranking quality while increasing inference cost. "
        "This baseline should remain optional until broader evaluation and latency review are complete.",
        "",
        "## 11. Recommendation",
        "",
        comparison["recommendation"],
    ]
    return "\n".join(lines)


def _index_results(report: dict[str, Any], *, report_name: str) -> dict[str, dict[str, Any]]:
    results = report.get("results")
    if not isinstance(results, list):
        raise ValueError(f"{report_name} report is missing per-case results")
    indexed: dict[str, dict[str, Any]] = {}
    for result in results:
        if not isinstance(result, dict) or not result.get("case_id"):
            raise ValueError(f"{report_name} report contains a result without case_id")
        case_id = str(result["case_id"])
        if case_id in indexed:
            raise ValueError(
                f"{report_name} report contains duplicate case_id={case_id}; "
                "compare single-mode reports only"
            )
        indexed[case_id] = result
    return indexed


def _case_count(report: dict[str, Any]) -> int:
    value = report.get("case_count")
    if not isinstance(value, int):
        raise ValueError("Evaluation report is missing integer case_count")
    return value


def _single_retrieval_mode(report: dict[str, Any]) -> str | None:
    modes = report.get("retrieval_modes")
    if isinstance(modes, list) and len(modes) == 1:
        return str(modes[0])
    return None


def _compare_case(baseline: dict[str, Any], experiment: dict[str, Any]) -> dict[str, Any]:
    baseline_rank = _metric_value(baseline, "first_evidence_hit_rank")
    experiment_rank = _metric_value(experiment, "first_evidence_hit_rank")
    movement = _movement(baseline_rank, experiment_rank)
    baseline_top1 = _top1_hit(baseline)
    experiment_top1 = _top1_hit(experiment)
    return {
        "case_id": baseline["case_id"],
        "category": baseline.get("category"),
        "intent_type": baseline.get("intent_type"),
        "baseline_rank": baseline_rank,
        "experiment_rank": experiment_rank,
        "rank_delta": _rank_delta(baseline_rank, experiment_rank),
        "movement": movement,
        "newly_top1_hit": baseline_rank != 1 and experiment_rank == 1,
        "lost_top1_hit": baseline_rank == 1 and experiment_rank != 1,
        "evidence_hit@5_regression": (
            _metric_value(baseline, "evidence_hit@5") is True
            and _metric_value(experiment, "evidence_hit@5") is False
        ),
        "baseline_top1_page": baseline_top1.get("page"),
        "experiment_top1_page": experiment_top1.get("page"),
        "baseline_top1_section": baseline_top1.get("section"),
        "experiment_top1_section": experiment_top1.get("section"),
    }


def _movement(baseline_rank: Any, experiment_rank: Any) -> str:
    if baseline_rank is None and experiment_rank is None:
        return "unchanged"
    if baseline_rank is None:
        return "improved"
    if experiment_rank is None:
        return "regressed"
    if experiment_rank < baseline_rank:
        return "improved"
    if experiment_rank > baseline_rank:
        return "regressed"
    return "unchanged"


def _rank_delta(baseline_rank: Any, experiment_rank: Any) -> int | None:
    if isinstance(baseline_rank, int) and isinstance(experiment_rank, int):
        return baseline_rank - experiment_rank
    return None


def _metric_value(result: dict[str, Any], key: str) -> Any:
    metrics = result.get("metrics")
    return metrics.get(key) if isinstance(metrics, dict) else None


def _top1_hit(result: dict[str, Any]) -> dict[str, Any]:
    hits = result.get("raw_hits")
    if isinstance(hits, list) and hits and isinstance(hits[0], dict):
        return hits[0]
    return {}


def _overall_metric_rows(
    baseline: dict[str, Any],
    experiment: dict[str, Any],
) -> list[dict[str, Any]]:
    baseline_metrics = baseline.get("overall_metrics") or {}
    experiment_metrics = experiment.get("overall_metrics") or {}
    rows = [
        _delta_row(metric, baseline_metrics.get(metric), experiment_metrics.get(metric))
        for metric in CORE_METRICS
    ]
    rows.append(
        _delta_row(
            "elapsed_seconds",
            baseline.get("elapsed_seconds"),
            experiment.get("elapsed_seconds"),
        )
    )
    return rows


def _delta_row(metric: str, baseline: Any, experiment: Any) -> dict[str, Any]:
    delta = (
        float(experiment) - float(baseline)
        if _is_number(baseline) and _is_number(experiment)
        else None
    )
    return {
        "metric": metric,
        "baseline": baseline,
        "experiment": experiment,
        "delta": delta,
    }


def _decision_summary(rows: list[dict[str, Any]]) -> str:
    metrics = {row["metric"]: row for row in rows}
    top1_delta = metrics["evidence_hit@1"]["delta"]
    mrr_delta = metrics["mrr"]["delta"]
    top5_delta = metrics["evidence_hit@5"]["delta"]
    if _positive(top1_delta) and _positive(mrr_delta) and _non_negative(top5_delta):
        return "Rerank improved top-1 ranking quality while preserving top-5 evidence recall."
    if _positive(top1_delta) and _positive(mrr_delta) and _negative(top5_delta):
        return (
            "Warning: Rerank improved ranking but reduced top-5 evidence recall. "
            "This requires case-level review before enabling by default."
        )
    return "Warning: Rerank did not improve primary ranking metrics on this evaluation set."


def _recommendation(rows: list[dict[str, Any]], summary: dict[str, int]) -> str:
    decision = _decision_summary(rows)
    if decision.startswith("Rerank improved") and summary["evidence_hit@5_regressions"] == 0:
        return (
            "Keep rerank as an optional feature; do not enable it by default yet. "
            "Expand the evaluation set before changing default behavior, and continue "
            "latency optimization and case-level review."
        )
    return (
        "Keep rerank disabled by default. Review regressed cases and top-5 recall changes "
        "before considering broader use."
    )


def _group_delta_rows(
    baseline_results,
    experiment_results,
    *,
    group_field: str,
) -> list[dict[str, Any]]:
    baseline_groups = _group_results(baseline_results, group_field=group_field)
    experiment_groups = _group_results(experiment_results, group_field=group_field)
    rows: list[dict[str, Any]] = []
    for group in sorted(set(baseline_groups) | set(experiment_groups)):
        baseline_metrics = _aggregate_case_results(baseline_groups.get(group, []))
        experiment_metrics = _aggregate_case_results(experiment_groups.get(group, []))
        rows.append(
            {
                "group": group,
                "case_count": len(baseline_groups.get(group, [])),
                "evidence_hit@1_baseline": baseline_metrics.get("evidence_hit@1"),
                "evidence_hit@1_experiment": experiment_metrics.get("evidence_hit@1"),
                "evidence_hit@1_delta": _numeric_delta(
                    baseline_metrics.get("evidence_hit@1"),
                    experiment_metrics.get("evidence_hit@1"),
                ),
                "mrr_baseline": baseline_metrics.get("mrr"),
                "mrr_experiment": experiment_metrics.get("mrr"),
                "mrr_delta": _numeric_delta(
                    baseline_metrics.get("mrr"),
                    experiment_metrics.get("mrr"),
                ),
            }
        )
    return rows


def _group_results(results, *, group_field: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in results:
        grouped[str(result.get(group_field) or "N/A")].append(result)
    return grouped


def _aggregate_case_results(results: list[dict[str, Any]]) -> dict[str, float]:
    aggregated: dict[str, float] = {}
    for metric in ("evidence_hit@1", "mrr"):
        values = []
        for result in results:
            value = _metric_value(result, metric)
            if isinstance(value, bool):
                values.append(1.0 if value else 0.0)
            elif _is_number(value):
                values.append(float(value))
        if values:
            aggregated[metric] = mean(values)
    return aggregated


def _latency_summary(
    baseline: dict[str, Any],
    experiment: dict[str, Any],
    case_count: int,
) -> list[dict[str, Any]]:
    baseline_elapsed = baseline.get("elapsed_seconds")
    experiment_elapsed = experiment.get("elapsed_seconds")
    return [
        _latency_row("elapsed_seconds", baseline_elapsed, experiment_elapsed),
        _latency_row(
            "average_seconds_per_case",
            _divide(baseline_elapsed, case_count),
            _divide(experiment_elapsed, case_count),
        ),
    ]


def _latency_row(metric: str, baseline: Any, experiment: Any) -> dict[str, Any]:
    return {
        **_delta_row(metric, baseline, experiment),
        "ratio": (
            float(experiment) / float(baseline)
            if _is_number(baseline) and _is_number(experiment) and float(baseline) != 0.0
            else None
        ),
    }


def _metadata_table(metadata: dict[str, tuple[Any, Any]]) -> str:
    lines = ["| item | baseline | experiment |", "| --- | --- | --- |"]
    for item, (baseline, experiment) in metadata.items():
        lines.append(f"| {item} | {_format_value(baseline)} | {_format_value(experiment)} |")
    return "\n".join(lines)


def _metric_delta_table(rows: list[dict[str, Any]]) -> str:
    lines = ["| metric | baseline | experiment | delta |", "| --- | ---: | ---: | ---: |"]
    for row in rows:
        lines.append(
            f"| {row['metric']} | {_format_value(row['baseline'])} | "
            f"{_format_value(row['experiment'])} | {_format_delta(row['delta'])} |"
        )
    return "\n".join(lines)


def _movement_summary_table(summary: dict[str, int]) -> str:
    lines = ["| item | count |", "| --- | ---: |"]
    for item, count in summary.items():
        lines.append(f"| {item} | {count} |")
    return "\n".join(lines)


def _case_movement_table(rows: list[dict[str, Any]], *, empty_message: str) -> str:
    if not rows:
        return empty_message
    columns = (
        "case_id",
        "category",
        "intent_type",
        "baseline_rank",
        "experiment_rank",
        "rank_delta",
        "baseline_top1_page",
        "experiment_top1_page",
        "baseline_top1_section",
        "experiment_top1_section",
    )
    return _dict_table(rows, columns)


def _unchanged_case_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No unchanged non-top1 cases found."
    columns = (
        "case_id",
        "category",
        "intent_type",
        "baseline_rank",
        "experiment_rank",
        "baseline_top1_section",
        "experiment_top1_section",
    )
    return _dict_table(rows, columns)


def _group_delta_table(rows: list[dict[str, Any]], *, group_label: str) -> str:
    if not rows:
        return "_No groups._"
    renamed = [{group_label: row["group"], **row} for row in rows]
    columns = (
        group_label,
        "case_count",
        "evidence_hit@1_baseline",
        "evidence_hit@1_experiment",
        "evidence_hit@1_delta",
        "mrr_baseline",
        "mrr_experiment",
        "mrr_delta",
    )
    return _dict_table(renamed, columns)


def _latency_table(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| metric | baseline | experiment | delta | ratio |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['metric']} | {_format_value(row['baseline'])} | "
            f"{_format_value(row['experiment'])} | {_format_delta(row['delta'])} | "
            f"{_format_ratio(row['ratio'])} |"
        )
    return "\n".join(lines)


def _dict_table(rows: list[dict[str, Any]], columns: tuple[str, ...]) -> str:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---:" if _numeric_column(column) else "---" for column in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_format_value(row.get(column)) for column in columns) + " |")
    return "\n".join(lines)


def _improved_sort_key(row: dict[str, Any]) -> tuple[bool, int]:
    return (not row["newly_top1_hit"], -(row["rank_delta"] or 0))


def _regressed_sort_key(row: dict[str, Any]) -> tuple[bool, int]:
    return (not row["lost_top1_hit"], row["rank_delta"] or 0)


def _numeric_column(column: str) -> bool:
    return (
        column.endswith("_rank")
        or column.endswith("_page")
        or column.endswith("_delta")
        or column.endswith("_baseline")
        or column.endswith("_experiment")
        or column == "case_count"
    )


def _format_value(value: Any) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _format_delta(value: Any) -> str:
    return f"{value:+.4f}" if _is_number(value) else "N/A"


def _format_ratio(value: Any) -> str:
    return f"{value:.2f}x" if _is_number(value) else "N/A"


def _numeric_delta(baseline: Any, experiment: Any) -> float | None:
    if not _is_number(baseline) or not _is_number(experiment):
        return None
    return float(experiment) - float(baseline)


def _divide(value: Any, denominator: int) -> float | None:
    if not _is_number(value) or denominator <= 0:
        return None
    return float(value) / denominator


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _positive(value: Any) -> bool:
    return _is_number(value) and float(value) > 0


def _negative(value: Any) -> bool:
    return _is_number(value) and float(value) < 0


def _non_negative(value: Any) -> bool:
    return _is_number(value) and float(value) >= 0


if __name__ == "__main__":
    main()
