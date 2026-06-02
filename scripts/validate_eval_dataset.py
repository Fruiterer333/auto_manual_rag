import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.evaluation.schemas import EvalCase


CASE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*_\d{3}$")
ALLOWED_CATEGORIES = {
    "alarm_handling",
    "explanation",
    "location_query",
    "maintenance_check",
    "parameter_query",
    "procedure",
    "warning_notice",
}
ALLOWED_INTENT_TYPES = {
    "alarm_handling",
    "broad_usage_guidance",
    "concept_explanation",
    "forbidden_condition",
    "limit_parameter",
    "location_and_operation",
    "location_and_parameter",
    "location_query",
    "maintenance_guidance",
    "safety_notice",
    "specific_operation",
    "state_explanation",
}
VISUAL_DEPENDENT_TERMS = (
    "按钮图标",
    "第几个编号",
    "见图",
    "图示",
    "图标",
    "如图",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a manual evaluation JSONL dataset.")
    parser.add_argument("dataset", nargs="?", default="data/eval/manual_eval_set.jsonl")
    return parser.parse_args()


def main() -> None:
    dataset_path = Path(parse_args().dataset)
    cases, errors, warnings = load_and_validate(dataset_path)
    print(f"dataset={dataset_path}")
    print(f"case_count={len(cases)}")
    print(f"category_distribution={dict(sorted(Counter(case.category for case in cases).items()))}")
    print(
        "intent_type_distribution="
        f"{dict(sorted(Counter(case.intent_type for case in cases).items()))}"
    )
    duplicate_questions = _duplicates(case.question.strip() for case in cases)
    print(f"duplicate_questions={duplicate_questions}")
    visual_dependent_notes = [
        case.id
        for case in cases
        if "visual-dependent" in case.notes or "图示依赖" in case.notes
    ]
    print(f"visual_dependent_notes_count={len(visual_dependent_notes)}")
    print(f"visual_dependent_notes={visual_dependent_notes}")
    for warning in warnings:
        print(f"warning={warning}")
    for error in errors:
        print(f"error={error}")
    if errors:
        raise SystemExit(1)
    print("validation=passed")


def load_and_validate(dataset_path: Path) -> tuple[list[EvalCase], list[str], list[str]]:
    if not dataset_path.exists():
        return [], [f"dataset not found: {dataset_path}"], []

    cases: list[EvalCase] = []
    errors: list[str] = []
    warnings: list[str] = []
    seen_ids: set[str] = set()
    for line_number, raw_line in enumerate(dataset_path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw_line.strip():
            continue
        try:
            payload = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_number}: invalid JSON: {exc}")
            continue
        try:
            case = EvalCase(**payload)
        except Exception as exc:
            errors.append(f"line {line_number}: invalid schema: {exc}")
            continue

        if case.id in seen_ids:
            errors.append(f"line {line_number}: duplicate id: {case.id}")
        seen_ids.add(case.id)
        if not CASE_ID_PATTERN.fullmatch(case.id):
            errors.append(f"line {line_number}: invalid snake_case id with numeric suffix: {case.id}")
        if not case.question.strip():
            errors.append(f"line {line_number}: empty question: {case.id}")
        if not case.category.strip() or not case.intent_type.strip():
            errors.append(f"line {line_number}: empty category or intent_type: {case.id}")
        if case.category not in ALLOWED_CATEGORIES:
            errors.append(
                f"line {line_number}: unsupported category={case.category}: {case.id}"
            )
        if case.intent_type not in ALLOWED_INTENT_TYPES:
            errors.append(
                f"line {line_number}: unsupported intent_type={case.intent_type}: {case.id}"
            )
        if not case.evidence:
            errors.append(f"line {line_number}: missing evidence: {case.id}")
        elif any(not evidence.quote.strip() for evidence in case.evidence):
            errors.append(f"line {line_number}: evidence quote is empty: {case.id}")
        if not any(
            [
                case.expected_pages,
                case.expected_sections,
                case.acceptable_sections,
                case.must_contain_terms,
                case.evidence,
            ]
        ):
            errors.append(f"line {line_number}: no retrieval evidence anchors: {case.id}")
        if any(evidence.section in {None, ""} for evidence in case.evidence):
            warnings.append(f"line {line_number}: evidence section metadata missing: {case.id}")
        visual_terms = [term for term in VISUAL_DEPENDENT_TERMS if term in case.question]
        if visual_terms:
            warnings.append(
                f"line {line_number}: visual-dependent question terms={visual_terms}: {case.id}"
            )
        cases.append(case)

    duplicate_questions = _duplicates(case.question.strip() for case in cases)
    if duplicate_questions:
        errors.append(f"duplicate questions: {duplicate_questions}")
    return cases, errors, warnings


def _duplicates(values) -> list[str]:
    counts = Counter(values)
    return sorted(value for value, count in counts.items() if count > 1)


if __name__ == "__main__":
    main()
