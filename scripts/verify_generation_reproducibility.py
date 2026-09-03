"""Verify repeated answer-generation stability with a frozen configuration."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings
from app.evaluation.answer_evaluator import (
    ANSWER_EVAL_SEMANTICS_VERSION,
    AnswerEvalCase,
    ensure_answer_eval_semantics_valid,
    load_answer_eval_cases,
)
from app.rag.chains.qa_chain import AnswerGenerationTrace, QAChain
from app.rag.llms.ollama_client import (
    collect_ollama_runtime_metadata,
    get_generation_request_metadata,
)


DEFAULT_DATASET = "data/eval/answer_eval_set.jsonl"
DEFAULT_CASE_IDS = (
    "abs_explanation_answer_001",
    "epb_enable_release_answer_001",
    "overspeed_condition_answer_001",
    "unsupported_voice_brake_calibration_answer_001",
)
DEFAULT_OUTPUT = "reports/evaluation/v4_5_1_generation_stability.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run repeated answer generation using an explicit Ollama configuration."
    )
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--case-id", action="append", dest="case_ids")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--retrieval-mode", choices=("dense", "bm25", "hybrid"))
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    return parser.parse_args()


def select_stability_cases(
    cases: list[AnswerEvalCase],
    case_ids: tuple[str, ...],
) -> list[AnswerEvalCase]:
    by_id = {case.id: case for case in cases}
    missing = [case_id for case_id in case_ids if case_id not in by_id]
    if missing:
        raise ValueError(f"Stability cases are absent from the dataset: {missing}")
    return [by_id[case_id] for case_id in case_ids]


def trace_record(run_number: int, trace: AnswerGenerationTrace) -> dict[str, Any]:
    return {
        "run_number": run_number,
        "prompt_evidence_identity": [
            {
                "evidence_id": evidence.evidence_id,
                "order": evidence.order,
                "chunk_id": evidence.chunk_id,
            }
            for evidence in trace.prompt_evidence
        ],
        "raw_answer": trace.raw_answer,
        "final_answer": trace.final_answer,
    }


def summarize_case_runs(
    *,
    case: AnswerEvalCase,
    runs: list[dict[str, Any]],
) -> dict[str, Any]:
    raw_answers = [record["raw_answer"] for record in runs]
    final_answers = [record["final_answer"] for record in runs]
    evidence_identities = [
        json.dumps(record["prompt_evidence_identity"], ensure_ascii=False, sort_keys=True)
        for record in runs
    ]
    raw_match = len(set(raw_answers)) == 1
    final_match = len(set(final_answers)) == 1
    evidence_match = len(set(evidence_identities)) == 1
    return {
        "case_id": case.id,
        "question": case.question,
        "answer_type": case.answer_type,
        "runs": runs,
        "raw_answer_exact_match": raw_match,
        "final_answer_exact_match": final_match,
        "prompt_evidence_identity_exact_match": evidence_match,
        "case_stable": raw_match and final_match and evidence_match,
    }


def build_verification_artifact(
    *,
    status: str,
    settings_metadata: dict[str, Any],
    runtime_metadata: dict[str, Any],
    cases: list[dict[str, Any]],
    runs_per_case: int,
    environment_error: str | None = None,
) -> dict[str, Any]:
    all_stable = bool(cases) and all(case["case_stable"] for case in cases)
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "verification_status": status,
        "semantics_version": ANSWER_EVAL_SEMANTICS_VERSION,
        "runs_per_case": runs_per_case,
        "generation_configuration": settings_metadata,
        "ollama_runtime": runtime_metadata,
        "environment_error": environment_error,
        "case_count": len(cases),
        "cases": cases,
        "raw_answer_exact_match_all_cases": all_stable,
        "final_answer_exact_match_all_cases": all_stable,
        "prompt_evidence_identity_exact_match_all_cases": all_stable,
        "repeated_run_stability_verified": status == "VERIFIED" and all_stable,
    }


def render_verification_markdown(artifact: dict[str, Any]) -> str:
    lines = [
        "# V4.5.1 重复生成稳定性验证",
        "",
        f"- 验证状态：`{artifact['verification_status']}`",
        f"- V4.3 语义版本：`{artifact['semantics_version']}`",
        f"- 每条 case 运行次数：{artifact['runs_per_case']}",
        f"- case 数量：{artifact['case_count']}",
        "",
        "## Generation Configuration",
        "",
    ]
    for key, value in artifact["generation_configuration"].items():
        lines.append(f"- {key}: `{json.dumps(value, ensure_ascii=False)}`")
    lines.extend(["", "## Ollama Runtime", ""])
    for key, value in artifact["ollama_runtime"].items():
        lines.append(f"- {key}: `{json.dumps(value, ensure_ascii=False)}`")
    if artifact["environment_error"]:
        lines.extend(
            [
                "",
                "## 环境限制",
                "",
                artifact["environment_error"],
            ]
        )
    if artifact["cases"]:
        lines.extend(
            [
                "",
                "## Case 结果",
                "",
                "| case_id | raw exact | final exact | Evidence identity exact | stable |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for case in artifact["cases"]:
            lines.append(
                f"| `{case['case_id']}` | {case['raw_answer_exact_match']} | "
                f"{case['final_answer_exact_match']} | "
                f"{case['prompt_evidence_identity_exact_match']} | "
                f"{case['case_stable']} |"
            )
    lines.extend(
        [
            "",
            "## 判定",
            "",
            f"- REPEATED_RUN_STABILITY_VERIFIED = "
            f"{'YES' if artifact['repeated_run_stability_verified'] else 'NO'}",
            "- 完全相同的 raw/final output 仅能说明当前本机、当前 Ollama 版本、"
            "当前模型 digest 和当前后端下的重复运行稳定性，不代表跨机器或跨版本的普适确定性。",
        ]
    )
    return "\n".join(lines) + "\n"


def write_artifact(artifact: dict[str, Any], output_path: str | Path) -> tuple[Path, Path]:
    json_path = Path(output_path)
    markdown_path = json_path.with_suffix(".md")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_path.write_text(render_verification_markdown(artifact), encoding="utf-8")
    return json_path, markdown_path


def main() -> int:
    args = parse_args()
    if args.runs != 3:
        raise ValueError("V4.5.1 requires exactly three repeated runs per case.")

    settings = get_settings()
    generation_metadata = get_generation_request_metadata(settings)
    runtime_metadata = collect_ollama_runtime_metadata(settings)
    runtime_error = runtime_metadata.get("ollama_runtime_metadata_error")
    if runtime_error:
        artifact = build_verification_artifact(
            status="ENVIRONMENT_BLOCKED",
            settings_metadata=generation_metadata,
            runtime_metadata=runtime_metadata,
            cases=[],
            runs_per_case=args.runs,
            environment_error=(
                "无法取得当前 Ollama runtime identity，未执行任何 generation："
                f"{runtime_error}"
            ),
        )
        json_path, markdown_path = write_artifact(artifact, args.output)
        print(f"verification_status={artifact['verification_status']}")
        print(f"json_output={json_path}")
        print(f"markdown_output={markdown_path}")
        return 2

    selected_cases = select_stability_cases(
        load_answer_eval_cases(args.dataset, split="dev"),
        tuple(args.case_ids or DEFAULT_CASE_IDS),
    )
    ensure_answer_eval_semantics_valid(selected_cases)
    chain = QAChain(settings=settings)
    case_results: list[dict[str, Any]] = []
    for case in selected_cases:
        records = [
            trace_record(
                run_number,
                chain.answer_with_trace(
                    case.question,
                    top_k=args.top_k,
                    retrieval_mode=args.retrieval_mode or settings.RETRIEVAL_MODE,
                ),
            )
            for run_number in range(1, args.runs + 1)
        ]
        case_results.append(summarize_case_runs(case=case, runs=records))

    artifact = build_verification_artifact(
        status="VERIFIED",
        settings_metadata=generation_metadata,
        runtime_metadata=runtime_metadata,
        cases=case_results,
        runs_per_case=args.runs,
    )
    json_path, markdown_path = write_artifact(artifact, args.output)
    print(f"verification_status={artifact['verification_status']}")
    print(f"json_output={json_path}")
    print(f"markdown_output={markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
