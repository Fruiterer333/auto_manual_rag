import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings
from app.core.logger import get_logger
from app.data.schemas.models import RetrievedChunk
from app.evaluation.loader import load_eval_cases
from app.evaluation.metrics import aggregate_results, evaluate_case_retrieval, group_aggregate
from app.evaluation.schemas import EvalCase, EvalSummary, RetrievalEvalResult
from app.rag.embeddings.local_embedding import LocalEmbeddingClient
from app.rag.retrievers.chunk_filters import (
    deduplicate_chunks_by_content,
    filter_retrieval_chunks,
)
from app.rag.retrievers.context_selector import enforce_max_context_chars, select_contexts
from app.rag.retrievers.hybrid_retriever import HybridRetriever


logger = get_logger(__name__)
VALID_MODES = ("dense", "bm25", "hybrid")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate retrieval quality on manual eval set.")
    parser.add_argument("--dataset", default="data/eval/manual_eval_set.jsonl")
    parser.add_argument("--retrieval-mode", choices=VALID_MODES, default=None)
    parser.add_argument("--all-modes", action="store_true")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--category")
    parser.add_argument("--intent-type")
    parser.add_argument("--split", default="dev")
    parser.add_argument("--use-context-selection", action="store_true")
    parser.add_argument("--output")
    parser.add_argument("--output-format", choices=("json", "csv", "md"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_settings()
    modes = list(VALID_MODES) if args.all_modes else [args.retrieval_mode or settings.RETRIEVAL_MODE]
    _validate_modes(modes)

    cases = load_eval_cases(
        args.dataset,
        category=args.category,
        intent_type=args.intent_type,
        split=args.split,
        limit=args.limit,
    )
    if not cases:
        raise ValueError("No evaluation cases matched the provided filters.")

    start_time = perf_counter()
    retriever = HybridRetriever(settings)
    embedding_client = _maybe_load_embedding_client(modes, settings)
    all_results: list[RetrievalEvalResult] = []
    for mode in modes:
        for case in cases:
            raw_contexts, final_contexts = _retrieve_for_case(
                case,
                mode=mode,
                top_k=args.top_k,
                use_context_selection=args.use_context_selection,
                retriever=retriever,
                embedding_client=embedding_client,
                settings=settings,
            )
            all_results.append(
                evaluate_case_retrieval(
                    case,
                    raw_contexts,
                    retrieval_mode=mode,
                    top_k=args.top_k,
                    final_contexts=final_contexts,
                    use_context_selection=args.use_context_selection,
                )
            )

    summary = EvalSummary(
        dataset_path=args.dataset,
        case_count=len(cases),
        retrieval_modes=modes,
        top_k=args.top_k,
        use_context_selection=args.use_context_selection,
        overall_metrics=aggregate_results(all_results),
        by_retrieval_mode=group_aggregate(all_results, field="retrieval_mode"),
        by_category=group_aggregate(all_results, field="category"),
        by_intent_type=group_aggregate(all_results, field="intent_type"),
        results=all_results,
    )
    elapsed = perf_counter() - start_time
    output_text = _format_markdown_report(summary, elapsed_seconds=elapsed)
    if args.output:
        output_path = _write_report(
            summary,
            output_path=Path(args.output),
            output_format=args.output_format,
            elapsed_seconds=elapsed,
        )
        print(output_text)
        print(f"\nreport_output={output_path}")
    else:
        print(output_text)

    logger.info(
        "Retrieval evaluation completed: dataset=%s cases=%s modes=%s top_k=%s context_selection=%s elapsed=%.2fs",
        args.dataset,
        len(cases),
        modes,
        args.top_k,
        args.use_context_selection,
        elapsed,
    )


def _retrieve_for_case(
    case: EvalCase,
    *,
    mode: str,
    top_k: int,
    use_context_selection: bool,
    retriever: HybridRetriever,
    embedding_client: LocalEmbeddingClient | None,
    settings,
) -> tuple[list[RetrievedChunk], list[RetrievedChunk] | None]:
    candidate_k = top_k
    if use_context_selection:
        candidate_k = max(top_k, settings.CONTEXT_SELECTION_CANDIDATE_K)
    query_embedding: list[float] = []
    if mode in {"dense", "hybrid"}:
        if embedding_client is None:
            raise ValueError(f"Embedding client is required for retrieval_mode={mode}")
        query_embedding = embedding_client.embed_query(case.question)

    retrieved = retriever.search(
        question=case.question,
        query_embedding=query_embedding,
        top_k=candidate_k,
        candidate_k=candidate_k,
        retrieval_mode=mode,
    )
    if not use_context_selection:
        return retrieved[:top_k], None

    filtered, _ = filter_retrieval_chunks(retrieved, stage="evaluation_context_selection_pre")
    deduped, _ = deduplicate_chunks_by_content(
        filtered,
        stage="evaluation_context_selection_pre",
    )
    selected = select_contexts(
        question=case.question,
        retrieved=deduped,
        top_k=top_k,
        enabled=True,
    )
    selected, _ = filter_retrieval_chunks(selected, stage="evaluation_final_context_pre")
    selected, _ = deduplicate_chunks_by_content(selected, stage="evaluation_final_context_pre")
    selected = enforce_max_context_chars(selected, max_chars=settings.MAX_CONTEXT_CHARS)
    return retrieved[:top_k], selected[:top_k]


def _maybe_load_embedding_client(
    modes: list[str],
    settings,
) -> LocalEmbeddingClient | None:
    if any(mode in {"dense", "hybrid"} for mode in modes):
        return LocalEmbeddingClient(settings)
    return None


def _validate_modes(modes: list[str]) -> None:
    invalid = [mode for mode in modes if mode not in VALID_MODES]
    if invalid:
        raise ValueError(f"Invalid retrieval modes: {invalid}")


def _write_report(
    summary: EvalSummary,
    *,
    output_path: Path,
    output_format: str | None,
    elapsed_seconds: float,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_format = output_format or _infer_format(output_path)
    if report_format == "json":
        payload = summary.model_dump()
        payload["generated_at"] = datetime.now().isoformat(timespec="seconds")
        payload["elapsed_seconds"] = elapsed_seconds
        output_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    elif report_format == "csv":
        _write_csv(summary.results, output_path)
    else:
        output_path.write_text(
            _format_markdown_report(summary, elapsed_seconds=elapsed_seconds),
            encoding="utf-8",
        )
    return output_path


def _infer_format(output_path: Path) -> str:
    suffix = output_path.suffix.lower().lstrip(".")
    if suffix in {"json", "csv", "md"}:
        return suffix
    return "md"


def _write_csv(results: list[RetrievalEvalResult], output_path: Path) -> None:
    metric_keys = sorted({key for result in results for key in result.metrics})
    fieldnames = [
        "case_id",
        "question",
        "category",
        "intent_type",
        "retrieval_mode",
        "top_k",
        "use_context_selection",
        *metric_keys,
        "failure_reasons",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            row: dict[str, Any] = {
                "case_id": result.case_id,
                "question": result.question,
                "category": result.category,
                "intent_type": result.intent_type,
                "retrieval_mode": result.retrieval_mode,
                "top_k": result.top_k,
                "use_context_selection": result.use_context_selection,
                "failure_reasons": ",".join(result.failure_reasons),
            }
            row.update(result.metrics)
            writer.writerow(row)


def _format_markdown_report(summary: EvalSummary, *, elapsed_seconds: float) -> str:
    lines = [
        "# Retrieval Evaluation Report",
        "",
        f"- generated_at: {datetime.now().isoformat(timespec='seconds')}",
        f"- dataset: `{summary.dataset_path}`",
        f"- case_count: {summary.case_count}",
        f"- retrieval_modes: {', '.join(summary.retrieval_modes)}",
        f"- top_k: {summary.top_k}",
        f"- use_context_selection: {summary.use_context_selection}",
        f"- elapsed_seconds: {elapsed_seconds:.2f}",
        "",
        "## Overall Metrics",
        "",
        _metrics_table(summary.overall_metrics),
        "",
        "## By Retrieval Mode",
        "",
        _retrieval_mode_table(summary.by_retrieval_mode),
        "",
    ]
    comparison_rows = _build_cross_mode_comparison(summary.results)
    if comparison_rows:
        lines.extend(
            [
                "## Mode Winners Summary",
                "",
                _mode_winners_summary_table(comparison_rows),
                "",
                "## Cross-mode Case Comparison",
                "",
                _cross_mode_comparison_table(comparison_rows),
                "",
                "## Hybrid Regressions",
                "",
                _hybrid_regressions_table(comparison_rows),
                "",
                "## Top-5 Hit but Not Top-1 Cases",
                "",
                _top5_not_top1_table(comparison_rows),
                "",
                "## Section Metadata Missing Cases",
                "",
                _section_metadata_missing_table(comparison_rows),
                "",
            ]
        )
    lines.extend(
        [
            "## By Category",
            "",
            _group_table(summary.by_category),
            "",
            "## By Intent Type",
            "",
            _group_table(summary.by_intent_type),
            "",
            "## Failure Cases",
            "",
        ]
    )
    failures = [result for result in summary.results if result.failure_reasons]
    if not failures:
        lines.append("No failure cases by current coarse criteria.")
    else:
        for result in failures[:50]:
            lines.append(
                f"- `{result.case_id}` mode={result.retrieval_mode} reasons={','.join(result.failure_reasons)} question={result.question}"
            )
    return "\n".join(lines)


def _metrics_table(metrics: dict[str, float | int | None]) -> str:
    if not metrics:
        return "_No metrics._"
    lines = ["| metric | value |", "| --- | ---: |"]
    for key, value in sorted(metrics.items()):
        lines.append(f"| {key} | {_format_value(value)} |")
    return "\n".join(lines)


def _group_table(groups: dict[str, dict[str, float | int | None]]) -> str:
    if not groups:
        return "_No groups._"
    preferred = [
        "case_count",
        "evidence_hit@1",
        "evidence_hit@3",
        "evidence_hit@5",
        "mrr",
        "term_coverage_ratio@5",
        "noise_rate@5",
        "duplicate_chunk_id_rate@5",
        "same_page_duplicate_rate@5",
        "cross_page_repeated_content_rate@5",
        "final_context_hit",
    ]
    lines = ["| group | " + " | ".join(preferred) + " |"]
    lines.append("| --- | " + " | ".join(["---:"] * len(preferred)) + " |")
    for group, metrics in sorted(groups.items()):
        values = [_format_value(metrics.get(key)) for key in preferred]
        lines.append(f"| {group} | " + " | ".join(values) + " |")
    return "\n".join(lines)


def _retrieval_mode_table(groups: dict[str, dict[str, float | int | None]]) -> str:
    if not groups:
        return "_No retrieval modes._"
    preferred = [
        "case_count",
        "evidence_hit@1",
        "evidence_hit@3",
        "evidence_hit@5",
        "mrr",
        "average_first_hit_rank",
        "expected_section_hit@5",
        "acceptable_section_hit@5",
        "any_term_hit@5",
        "all_terms_hit@5",
        "term_coverage_ratio@5",
        "noise_rate@5",
        "duplicate_chunk_id_rate@5",
        "same_page_duplicate_rate@5",
        "cross_page_repeated_content_rate@5",
        "final_context_hit",
    ]
    lines = ["| retrieval_mode | " + " | ".join(preferred) + " |"]
    lines.append("| --- | " + " | ".join(["---:"] * len(preferred)) + " |")
    for mode, metrics in sorted(groups.items()):
        values = [_format_value(metrics.get(key)) for key in preferred]
        lines.append(f"| {mode} | " + " | ".join(values) + " |")
    return "\n".join(lines)


def _build_cross_mode_comparison(
    results: list[RetrievalEvalResult],
) -> list[dict[str, Any]]:
    grouped: dict[str, list[RetrievalEvalResult]] = defaultdict(list)
    for result in results:
        grouped[result.case_id].append(result)
    if len({result.retrieval_mode for result in results}) <= 1:
        return []

    rows: list[dict[str, Any]] = []
    for case_id, case_results in grouped.items():
        by_mode = {result.retrieval_mode: result for result in case_results}
        ranks = {
            mode: _first_hit_rank(by_mode.get(mode))
            for mode in VALID_MODES
        }
        top_hits = {
            mode: _top_hit(by_mode.get(mode))
            for mode in VALID_MODES
        }
        notes = _comparison_notes(ranks, top_hits)
        first_result = case_results[0]
        rows.append(
            {
                "case_id": case_id,
                "category": first_result.category,
                "intent_type": first_result.intent_type,
                "dense_rank": ranks["dense"],
                "bm25_rank": ranks["bm25"],
                "hybrid_rank": ranks["hybrid"],
                "best_mode": _best_modes(ranks),
                "worst_mode": _worst_modes(ranks),
                "dense_top1_page": _hit_value(top_hits["dense"], "page"),
                "bm25_top1_page": _hit_value(top_hits["bm25"], "page"),
                "hybrid_top1_page": _hit_value(top_hits["hybrid"], "page"),
                "dense_top1_section": _hit_value(top_hits["dense"], "section"),
                "bm25_top1_section": _hit_value(top_hits["bm25"], "section"),
                "hybrid_top1_section": _hit_value(top_hits["hybrid"], "section"),
                "comparison_note": ",".join(notes),
            }
        )
    return sorted(rows, key=_comparison_sort_key)


def _comparison_notes(
    ranks: dict[str, int | None],
    top_hits: dict[str, Any],
) -> list[str]:
    notes: list[str] = []
    available_ranks = [rank for rank in ranks.values() if rank is not None]
    all_modes_present = all(mode in ranks and ranks[mode] is not None for mode in VALID_MODES)
    if not available_ranks:
        return ["all_failed"]
    if all(rank == 1 for rank in ranks.values()):
        notes.append("all_top1_hit")
    elif all_modes_present:
        notes.append("all_hit_within_top5")
    if _is_worse(ranks["hybrid"], ranks["bm25"]):
        notes.append("hybrid_worse_than_bm25")
    if _is_worse(ranks["hybrid"], ranks["dense"]):
        notes.append("hybrid_worse_than_dense")
    best_modes = _best_modes(ranks)
    if "," not in best_modes and best_modes != "N/A":
        notes.append(f"{best_modes}_best")
    if min(available_ranks) > 1:
        notes.append("top5_hit_but_no_top1")
    if any(hit is not None and not hit.section for hit in top_hits.values()):
        notes.append("section_metadata_missing")
    return notes


def _first_hit_rank(result: RetrievalEvalResult | None) -> int | None:
    if result is None:
        return None
    rank = result.metrics.get("first_evidence_hit_rank")
    return int(rank) if isinstance(rank, (int, float)) else None


def _top_hit(result: RetrievalEvalResult | None) -> Any:
    if result is None or not result.raw_hits:
        return None
    return result.raw_hits[0]


def _hit_value(hit: Any, field: str) -> Any:
    return getattr(hit, field) if hit is not None else None


def _best_modes(ranks: dict[str, int | None]) -> str:
    hits = {mode: rank for mode, rank in ranks.items() if rank is not None}
    if not hits:
        return "N/A"
    best_rank = min(hits.values())
    return ",".join(mode for mode in VALID_MODES if hits.get(mode) == best_rank)


def _worst_modes(ranks: dict[str, int | None]) -> str:
    if all(rank is None for rank in ranks.values()):
        return "all_failed"
    missing_modes = [mode for mode in VALID_MODES if ranks[mode] is None]
    if missing_modes:
        return ",".join(missing_modes)
    worst_rank = max(rank for rank in ranks.values() if rank is not None)
    return ",".join(mode for mode in VALID_MODES if ranks[mode] == worst_rank)


def _is_worse(candidate: int | None, baseline: int | None) -> bool:
    return baseline is not None and (candidate is None or candidate > baseline)


def _comparison_sort_key(row: dict[str, Any]) -> tuple[int, int, int, str]:
    notes = row["comparison_note"].split(",")
    return (
        0 if "all_failed" in notes else 1,
        0 if any(note.startswith("hybrid_worse_than_") for note in notes) else 1,
        0 if "top5_hit_but_no_top1" in notes else 1,
        row["case_id"],
    )


def _cross_mode_comparison_table(rows: list[dict[str, Any]]) -> str:
    headers = [
        "case_id",
        "category",
        "intent_type",
        "dense_rank",
        "bm25_rank",
        "hybrid_rank",
        "best_mode",
        "worst_mode",
        "dense_top1_page",
        "bm25_top1_page",
        "hybrid_top1_page",
        "dense_top1_section",
        "bm25_top1_section",
        "hybrid_top1_section",
        "comparison_note",
    ]
    return _comparison_rows_table(rows, headers)


def _mode_winners_summary_table(rows: list[dict[str, Any]]) -> str:
    items = [
        "all_top1_hit",
        "bm25_best",
        "dense_best",
        "hybrid_best",
        "tied_best",
        "hybrid_worse_than_bm25",
        "hybrid_worse_than_dense",
        "top5_hit_but_no_top1",
        "all_failed",
        "section_metadata_missing",
    ]
    counts = {item: 0 for item in items}
    for row in rows:
        notes = _row_notes(row)
        for item in items:
            if item in notes:
                counts[item] += 1
        if "," in row["best_mode"]:
            counts["tied_best"] += 1
    lines = ["| item | count |", "| --- | ---: |"]
    for item in items:
        lines.append(f"| {item} | {counts[item]} |")
    return "\n".join(lines)


def _hybrid_regressions_table(rows: list[dict[str, Any]]) -> str:
    selected = [
        row
        for row in rows
        if {"hybrid_worse_than_bm25", "hybrid_worse_than_dense"} & _row_notes(row)
    ]
    if not selected:
        return "No hybrid regression cases found."
    headers = [
        "case_id",
        "category",
        "intent_type",
        "dense_rank",
        "bm25_rank",
        "hybrid_rank",
        "best_mode",
        "dense_top1_page",
        "bm25_top1_page",
        "hybrid_top1_page",
        "dense_top1_section",
        "bm25_top1_section",
        "hybrid_top1_section",
        "comparison_note",
    ]
    return _comparison_rows_table(selected, headers)


def _top5_not_top1_table(rows: list[dict[str, Any]]) -> str:
    selected = [row for row in rows if "top5_hit_but_no_top1" in _row_notes(row)]
    if not selected:
        return "No top-5-hit-but-not-top-1 cases found."
    headers = [
        "case_id",
        "category",
        "intent_type",
        "dense_rank",
        "bm25_rank",
        "hybrid_rank",
        "best_mode",
        "worst_mode",
        "dense_top1_page",
        "bm25_top1_page",
        "hybrid_top1_page",
        "dense_top1_section",
        "bm25_top1_section",
        "hybrid_top1_section",
        "comparison_note",
    ]
    return _comparison_rows_table(selected, headers)


def _section_metadata_missing_table(rows: list[dict[str, Any]]) -> str:
    selected = [row for row in rows if "section_metadata_missing" in _row_notes(row)]
    if not selected:
        return "No section metadata missing cases found."
    headers = [
        "case_id",
        "category",
        "intent_type",
        "dense_top1_page",
        "bm25_top1_page",
        "hybrid_top1_page",
        "dense_top1_section",
        "bm25_top1_section",
        "hybrid_top1_section",
        "comparison_note",
    ]
    return _comparison_rows_table(selected, headers)


def _row_notes(row: dict[str, Any]) -> set[str]:
    return {note for note in row["comparison_note"].split(",") if note}


def _comparison_rows_table(rows: list[dict[str, Any]], headers: list[str]) -> str:
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        values = [_format_value(row.get(header)) for header in headers]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def _format_value(value: Any) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


if __name__ == "__main__":
    main()
