import json

from app.evaluation.loader import load_eval_cases


def _payload(case_id: str, *, excluded: bool = False) -> dict:
    return {
        "id": case_id,
        "question": "测试问题",
        "category": "explanation",
        "intent_type": "state_explanation",
        "evidence": [],
        "split": "dev",
        "excluded": excluded,
        "exclusion_reason": "Evidence is absent." if excluded else "",
    }


def test_loader_excludes_disabled_cases_from_active_denominator(tmp_path) -> None:
    dataset = tmp_path / "eval.jsonl"
    dataset.write_text(
        "\n".join(
            json.dumps(payload, ensure_ascii=False)
            for payload in (_payload("active"), _payload("excluded", excluded=True))
        )
        + "\n",
        encoding="utf-8",
    )

    active_cases = load_eval_cases(dataset, split="dev")
    all_cases = load_eval_cases(dataset, split="dev", include_excluded=True)

    assert [case.id for case in active_cases] == ["active"]
    assert [case.id for case in all_cases] == ["active", "excluded"]
