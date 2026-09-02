import json
from pathlib import Path

from app.core.logger import get_logger
from app.evaluation.schemas import EvalCase


logger = get_logger(__name__)


def load_eval_cases(
    dataset_path: str | Path,
    *,
    category: str | None = None,
    intent_type: str | None = None,
    split: str | None = None,
    limit: int | None = None,
    include_excluded: bool = False,
) -> list[EvalCase]:
    path = Path(dataset_path)
    if not path.exists():
        raise FileNotFoundError(f"Evaluation dataset not found: {path}")

    cases: list[EvalCase] = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}: {exc}") from exc

            try:
                case = EvalCase(**payload)
            except Exception as exc:
                raise ValueError(f"Invalid eval case at {path}:{line_number}: {exc}") from exc

            if category and case.category != category:
                continue
            if intent_type and case.intent_type != intent_type:
                continue
            if split and case.split != split:
                continue
            if case.excluded and not include_excluded:
                continue

            _warn_if_case_is_hard_to_evaluate(case)
            cases.append(case)
            if limit is not None and len(cases) >= limit:
                break

    logger.info(
        "Evaluation dataset loaded: path=%s cases=%s category=%s intent_type=%s split=%s limit=%s include_excluded=%s",
        path,
        len(cases),
        category,
        intent_type,
        split,
        limit,
        include_excluded,
    )
    return cases


def _warn_if_case_is_hard_to_evaluate(case: EvalCase) -> None:
    if not case.evidence:
        logger.warning("Eval case has no evidence: id=%s", case.id)
    elif any(not item.quote for item in case.evidence):
        logger.warning("Eval case has evidence without quote: id=%s", case.id)

    has_retrieval_anchor = any(
        [
            case.expected_pages,
            case.expected_sections,
            case.acceptable_sections,
            case.must_contain_terms,
            case.evidence,
        ]
    )
    if not has_retrieval_anchor:
        logger.warning("Eval case has weak retrieval anchors: id=%s", case.id)
