import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings
from app.evaluation.benchmark_validation import ensure_retrieval_benchmark_valid
from app.evaluation.loader import load_eval_cases
from app.rag.retrievers.bm25_retriever import BM25Retriever


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate retrieval gold chunks against the current BM25 chunk store."
    )
    parser.add_argument("--dataset", default="data/eval/manual_eval_set.jsonl")
    parser.add_argument("--split", default="dev")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cases = load_eval_cases(args.dataset, split=args.split, include_excluded=True)
    retriever = BM25Retriever(get_settings())
    retriever.load_index()
    result = ensure_retrieval_benchmark_valid(cases, retriever.chunks)
    print(f"benchmark_cases={result.case_count}")
    print(f"benchmark_excluded_cases={result.excluded_case_count}")
    print(f"benchmark_evidence={result.evidence_count}")
    print(f"benchmark_valid={result.valid}")
    print(f"issue_counts={result.issue_counts}")


if __name__ == "__main__":
    main()
