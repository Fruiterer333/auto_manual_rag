import argparse
import csv
import json
import sys
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


def _format_value(value: float | int | None) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


if __name__ == "__main__":
    main()
