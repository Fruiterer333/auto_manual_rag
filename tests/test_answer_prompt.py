from app.data.schemas.models import Chunk
from app.rag.prompts.answer_prompt import (
    DEFAULT_MAX_CONTEXTS,
    DEFAULT_MAX_CONTEXT_CHARS,
    build_answer_prompt,
)


def _chunk(
    chunk_id: str,
    text: str,
    *,
    page: int | None = 10,
    chapter: str | None = "启动和驾驶",
    section: str | None = "电子驻车制动（EPB）",
    subsection: str | None = "EPB AUTO功能",
    content_type: str | None = "normal",
    heading_path=None,
) -> Chunk:
    metadata = {}
    if heading_path is not None:
        metadata["heading_path"] = heading_path
    return Chunk(
        chunk_id=chunk_id,
        doc_id=f"doc-{chunk_id}",
        source_file="manual.pdf",
        page=page,
        chapter=chapter,
        section=section,
        subsection=subsection,
        content_type=content_type,
        text=text,
        metadata=metadata,
    )


def test_prompt_evidence_contains_metadata_and_content_fields() -> None:
    prompt = build_answer_prompt(
        "EPB AUTO功能是什么？",
        [
            _chunk(
                "chunk-1",
                "EPB AUTO功能开启后，车辆熄火时会自动启用电子驻车制动。",
                heading_path=["启动和驾驶", "电子驻车制动（EPB）", "EPB AUTO功能"],
            )
        ],
    )

    assert "[EVIDENCE E1]" in prompt
    assert "page: 10" in prompt
    assert "chapter: 启动和驾驶" in prompt
    assert "section: 电子驻车制动（EPB）" in prompt
    assert "subsection: EPB AUTO功能" in prompt
    assert "heading_path: 启动和驾驶 > 电子驻车制动（EPB） > EPB AUTO功能" in prompt
    assert "content_type: normal" in prompt
    assert "content:\nEPB AUTO功能开启后" in prompt
    assert "[/EVIDENCE]" in prompt


def test_prompt_evidence_ids_follow_final_order() -> None:
    prompt = build_answer_prompt(
        "如何操作？",
        [
            _chunk("chunk-1", "第一条证据。"),
            _chunk("chunk-2", "第二条证据。"),
            _chunk("chunk-3", "第三条证据。"),
        ],
    )

    assert prompt.index("[EVIDENCE E1]") < prompt.index("[EVIDENCE E2]")
    assert prompt.index("[EVIDENCE E2]") < prompt.index("[EVIDENCE E3]")
    assert prompt.index("第一条证据。") < prompt.index("第二条证据。")
    assert prompt.index("第二条证据。") < prompt.index("第三条证据。")


def test_prompt_forbids_internal_evidence_ids_in_final_answer() -> None:
    prompt = build_answer_prompt("如何操作？", [_chunk("chunk-1", "操作说明。")])

    assert "Evidence ID 仅用于内部判断" in prompt
    assert "最终回答不得输出 E1/E2" in prompt
    assert "CONTEXT" in prompt
    assert "source id" in prompt


def test_subsection_none_formats_as_na() -> None:
    prompt = build_answer_prompt(
        "普通说明是什么？",
        [
            _chunk(
                "chunk-1",
                "普通说明。",
                subsection=None,
                heading_path=["启动和驾驶", "电子驻车制动（EPB）"],
            )
        ],
    )

    assert "subsection: N/A" in prompt
    assert "heading_path: 启动和驾驶 > 电子驻车制动（EPB）" in prompt


def test_heading_path_list_is_not_rendered_as_python_list() -> None:
    prompt = build_answer_prompt(
        "如何操作？",
        [
            _chunk(
                "chunk-1",
                "操作说明。",
                heading_path=["驾驶辅助", "全自动泊车", "设置自动泊车界面"],
            )
        ],
    )

    assert "heading_path: 驾驶辅助 > 全自动泊车 > 设置自动泊车界面" in prompt
    assert "['驾驶辅助'" not in prompt


def test_context_count_limit_keeps_allowed_number_only() -> None:
    chunks = [_chunk(f"chunk-{index}", f"证据{index}。") for index in range(1, 5)]

    prompt = build_answer_prompt("如何操作？", chunks, max_contexts=2)

    assert "[EVIDENCE E1]" in prompt
    assert "[EVIDENCE E2]" in prompt
    assert "[EVIDENCE E3]" not in prompt
    assert "证据3。" not in prompt


def test_context_char_budget_skips_later_evidence_without_reordering() -> None:
    prompt = build_answer_prompt(
        "如何操作？",
        [
            _chunk("chunk-1", "短证据。"),
            _chunk("chunk-2", "这是一条会超过剩余预算的较长证据。"),
            _chunk("chunk-3", "不应越过第二条证据被加入。"),
        ],
        max_contexts=3,
        max_context_chars=6,
    )

    assert "[EVIDENCE E1]" in prompt
    assert "短证据。" in prompt
    assert "[EVIDENCE E2]" not in prompt
    assert "不应越过第二条证据被加入。" not in prompt


def test_first_evidence_is_truncated_when_it_exceeds_char_budget() -> None:
    prompt = build_answer_prompt(
        "如何操作？",
        [_chunk("chunk-1", "第一条证据内容很长，需要被截断。")],
        max_contexts=1,
        max_context_chars=12,
    )

    assert "[EVIDENCE E1]" in prompt
    assert "[TRUNCATED]" in prompt
    assert "truncated: true" in prompt


def test_prompt_contains_condition_difference_and_true_conflict_policy() -> None:
    prompt = build_answer_prompt("不同状态下如何操作？", [_chunk("chunk-1", "操作说明。")])

    assert "条件差异" in prompt
    assert "真正冲突" in prompt
    assert "不要自行裁决" in prompt
    assert "无法确定唯一结论" in prompt


def test_groundedness_rules_are_compact_and_keep_core_contract() -> None:
    prompt = build_answer_prompt("有哪些注意事项？", [_chunk("chunk-1", "■必须检查。")])

    assert "1. 仅依据下方 Evidence 回答" in prompt
    assert "我没有在手册中找到可靠依据" in prompt
    assert "不得省略或弱化" in prompt
    assert "优先按手册结构整理" in prompt
    assert "不得输出 E1/E2" in prompt
    assert "7." not in prompt
    assert DEFAULT_MAX_CONTEXTS == 5
    assert DEFAULT_MAX_CONTEXT_CHARS == 6000
