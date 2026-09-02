import argparse
import hashlib
import sys
from datetime import datetime
from pathlib import Path
from time import perf_counter


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings
from app.evaluation.answer_evaluator import (
    ANSWER_EVAL_SEMANTICS_VERSION,
    build_answer_evaluation_run,
    ensure_answer_eval_semantics_valid,
    evaluate_answer_response,
    load_answer_eval_cases,
    write_answer_evaluation_outputs,
)
from app.rag.chains.qa_chain import QAChain
from app.rag.llms.ollama_client import (
    collect_ollama_runtime_metadata,
    get_generation_request_metadata,
)
from app.rag.prompts.answer_prompt import DEFAULT_MAX_CONTEXTS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate answers and create an auditable answer evaluation report."
    )
    parser.add_argument("--dataset", default="data/eval/answer_eval_set.jsonl")
    parser.add_argument("--output")
    parser.add_argument("--json-output")
    parser.add_argument("--retrieval-mode", choices=("dense", "bm25", "hybrid"))
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--split", default="dev")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_settings()
    retrieval_mode = args.retrieval_mode or settings.RETRIEVAL_MODE
    markdown_path = (
        Path(args.output)
        if args.output
        else _default_output_path(
            retrieval_mode=retrieval_mode,
            rerank_enabled=settings.ENABLE_RERANK,
        )
    )
    cases = load_answer_eval_cases(args.dataset, limit=args.limit, split=args.split)
    if not cases:
        raise ValueError("No answer evaluation cases matched the provided filters.")
    ensure_answer_eval_semantics_valid(cases)
    generation_metadata = get_generation_request_metadata()
    ollama_runtime_metadata = collect_ollama_runtime_metadata(settings)

    chain = QAChain(settings=settings)
    results = []
    for case in cases:
        started = perf_counter()
        trace = chain.answer_with_trace(
            case.question,
            top_k=args.top_k,
            retrieval_mode=retrieval_mode,
        )
        results.append(
            evaluate_answer_response(
                case,
                trace.response,
                elapsed_seconds=perf_counter() - started,
                retrieval_mode=retrieval_mode,
                raw_answer=trace.raw_answer,
                prompt_evidence=trace.prompt_evidence,
            )
        )

    run = build_answer_evaluation_run(
        dataset_path=args.dataset,
        config={
            "retrieval_mode": retrieval_mode,
            "rerank_enabled": settings.ENABLE_RERANK,
            "embedding_model": settings.EMBEDDING_MODEL_NAME,
            "rerank_model": settings.RERANK_MODEL_NAME if settings.ENABLE_RERANK else None,
            "rerank_top_n": settings.RERANK_TOP_N if settings.ENABLE_RERANK else None,
            "rerank_output_top_k": (
                settings.RERANK_OUTPUT_TOP_K if settings.ENABLE_RERANK else None
            ),
            "llm_model": settings.OLLAMA_MODEL,
            "top_k": args.top_k,
            "max_contexts": min(args.top_k, DEFAULT_MAX_CONTEXTS),
            "max_context_chars": settings.MAX_CONTEXT_CHARS,
            "metadata_context_selection_enabled": (
                settings.ENABLE_METADATA_CONTEXT_SELECTION
            ),
            "neighbor_expansion_enabled": settings.ENABLE_NEIGHBOR_CONTEXT_EXPANSION,
            "answer_eval_dataset_sha256": _file_sha256(Path(args.dataset)),
            "answer_eval_semantics_version": ANSWER_EVAL_SEMANTICS_VERSION,
            **generation_metadata,
            **ollama_runtime_metadata,
        },
        results=results,
    )
    json_path = (
        Path(args.json_output)
        if args.json_output
        else markdown_path.with_suffix(".json")
    )
    written_markdown, written_json = write_answer_evaluation_outputs(
        run,
        markdown_path=markdown_path,
        json_path=json_path,
    )
    print(f"answer_eval_cases={len(results)}")
    print(f"markdown_output={written_markdown}")
    print(f"json_output={written_json}")


def _default_output_path(
    *,
    retrieval_mode: str,
    rerank_enabled: bool,
) -> Path:
    rerank_label = "rerank" if rerank_enabled else "no_rerank"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path(
        "reports/evaluation/"
        f"v4_answer_baseline_{retrieval_mode}_{rerank_label}_{timestamp}.md"
    )


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    main()
