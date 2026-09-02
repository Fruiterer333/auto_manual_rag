import pytest

from app.rag.utils.internal_evidence_refs import (
    contains_internal_evidence_reference,
    strip_internal_evidence_references,
)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Evidence E1：电子驻车制动可以手动释放。", "电子驻车制动可以手动释放。"),
        ("(Evidence E1)电子驻车制动可以手动释放。", "电子驻车制动可以手动释放。"),
        ("（Evidence E1）电子驻车制动可以手动释放。", "电子驻车制动可以手动释放。"),
        ("E1 Evidence, 电子驻车制动可以手动释放。", "电子驻车制动可以手动释放。"),
        ("证据E2：车辆应立即停车。", "车辆应立即停车。"),
        ("根据 Evidence E3，电子驻车制动可以手动释放。", "电子驻车制动可以手动释放。"),
        ("参考[EVIDENCE E2]，车辆应立即停车。", "车辆应立即停车。"),
        ("参见资料4，执行相应操作。", "执行相应操作。"),
        ("根据手册片段2，执行相应操作。", "执行相应操作。"),
        ("参考 source id 3，执行相应操作。", "执行相应操作。"),
        ("Evidence E1", ""),
    ],
)
def test_strip_internal_evidence_references(text: str, expected: str) -> None:
    assert strip_internal_evidence_references(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "故障代码 E1 表示传感器异常。",
        "E10 需要由维修人员处理。",
        "根据车辆状态进行操作。",
        "具体要求请参考用户手册。",
        "可参见车辆保养章节。",
    ],
)
def test_strip_preserves_non_internal_text(text: str) -> None:
    assert strip_internal_evidence_references(text) == text
    assert contains_internal_evidence_reference(text) is False


@pytest.mark.parametrize(
    "text",
    [
        "根据 Evidence E3，电子驻车制动可以手动释放。",
        "参照E3证据，执行相应操作。",
        "参考[EVIDENCE E2]，车辆应立即停车。",
        "Evidence E1",
    ],
)
def test_sanitizer_is_idempotent(text: str) -> None:
    cleaned = strip_internal_evidence_references(text)

    assert strip_internal_evidence_references(cleaned) == cleaned
