"""Create a derived V4.5-C artifact from a frozen baseline and final human labels."""

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.evaluation.answer_evaluator import AnswerEvaluationRun
from app.evaluation.human_adjudication import (
    build_human_adjudicated_run,
    load_human_adjudication_source,
    write_human_adjudication_outputs,
)


DEFAULT_BASELINE = (
    "reports/evaluation/v4_answer_baseline_hybrid_no_rerank_20260902_200054.json"
)
DEFAULT_ADJUDICATIONS = "data/eval/v4_5_b_human_adjudication.json"
DEFAULT_MARKDOWN_OUTPUT = "reports/evaluation/v4_5_c_human_adjudication_summary.md"
DEFAULT_JSON_OUTPUT = "reports/evaluation/v4_5_c_human_adjudicated_baseline.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Consolidate final human answer-evaluation adjudications."
    )
    parser.add_argument("--baseline", default=DEFAULT_BASELINE)
    parser.add_argument("--adjudications", default=DEFAULT_ADJUDICATIONS)
    parser.add_argument("--output", default=DEFAULT_MARKDOWN_OUTPUT)
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    baseline_path = Path(args.baseline)
    baseline = AnswerEvaluationRun.model_validate_json(
        baseline_path.read_text(encoding="utf-8")
    )
    adjudications = load_human_adjudication_source(args.adjudications)
    run = build_human_adjudicated_run(
        baseline,
        source_baseline_path=str(baseline_path),
        adjudication_source=adjudications,
    )
    markdown_path, json_path = write_human_adjudication_outputs(
        run,
        markdown_path=args.output,
        json_path=args.json_output,
    )
    print(f"adjudicated_case_count={run.case_count}")
    print(f"markdown_output={markdown_path}")
    print(f"json_output={json_path}")


if __name__ == "__main__":
    main()
