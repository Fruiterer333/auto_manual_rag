import pytest

from app.evaluation.answer_normalization import (
    normalize_answer_for_match,
    normalize_term_for_match,
    term_matches_answer,
)


@pytest.mark.parametrize(
    ("term", "answer"),
    [
        ("10 cm", "喷嘴应至少保持10cm距离。"),
        ("10 cm", "喷嘴应至少保持10厘米距离。"),
        ("10cm", "喷嘴应至少保持10 厘米距离。"),
        ("ＡＢＳ", "ABS发生故障。"),
        ("ABS", "abs发生故障。"),
        ("10  cm", "至少保持10 cm距离。"),
    ],
)
def test_conservative_term_normalization_matches_format_variants(
    term: str,
    answer: str,
) -> None:
    assert term_matches_answer(term, answer) is True


@pytest.mark.parametrize(
    ("term", "answer"),
    [
        ("10 cm", "喷嘴应至少保持30 cm距离。"),
        ("10 cm", "喷嘴应至少保持10 m距离。"),
        ("立即停车", "停车灯已点亮。"),
        ("ABS故障", "ABS工作正常。"),
        ("踩下制动踏板", "松开制动踏板。"),
    ],
)
def test_conservative_term_normalization_does_not_match_semantic_differences(
    term: str,
    answer: str,
) -> None:
    assert term_matches_answer(term, answer) is False


def test_normalization_returns_stable_comparison_forms() -> None:
    assert normalize_term_for_match("１０ cm") == "10cm"
    assert normalize_answer_for_match("ＡＢＳ： 正常") == "abs正常"
