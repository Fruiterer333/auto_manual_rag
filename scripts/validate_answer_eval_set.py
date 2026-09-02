import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings
from app.evaluation.answer_evaluator import (
    ensure_answer_eval_semantics_valid,
    load_answer_eval_cases,
)
from app.evaluation.answer_provenance_validation import (
    ensure_answer_eval_provenance_valid,
)
from app.evaluation.loader import load_eval_cases
from app.rag.retrievers.bm25_retriever import BM25Retriever


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Answer Evaluation evidence against the frozen retrieval cases and current corpus."
    )
    parser.add_argument("--dataset", default="data/eval/answer_eval_set.jsonl")
    parser.add_argument("--retrieval-dataset", default="data/eval/manual_eval_set.jsonl")
    parser.add_argument("--split", default="dev")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    answer_cases = load_answer_eval_cases(args.dataset, split=args.split)
    retrieval_cases = load_eval_cases(
        args.retrieval_dataset,
        split=args.split,
        include_excluded=True,
    )
    retriever = BM25Retriever(get_settings())
    retriever.load_index()
    chunks = list(retriever.chunks) + list(retriever.filtered_chunks)
    result = ensure_answer_eval_provenance_valid(
        answer_cases,
        retrieval_cases,
        chunks,
    )
    semantics_result = ensure_answer_eval_semantics_valid(answer_cases)
    print(f"answer_eval_cases={result.case_count}")
    print(f"positive_cases={result.positive_case_count}")
    print(f"hard_negative_cases={result.hard_negative_case_count}")
    print(f"answer_evidence={result.evidence_count}")
    print(f"provenance_valid={result.valid}")
    print(f"issue_counts={result.issue_counts}")
    print(f"answer_eval_semantics_version={semantics_result.semantics_version}")
    print(f"rubric_schema_valid={semantics_result.rubric_schema_valid}")
    print(
        "outstanding_contract_reviews="
        f"{semantics_result.outstanding_contract_reviews}"
    )
    print(f"semantics_valid={semantics_result.valid}")


if __name__ == "__main__":
    main()
