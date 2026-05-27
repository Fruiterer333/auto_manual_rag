import re
from collections import Counter
from typing import Any

from app.core.logger import get_logger
from app.data.schemas.models import Chunk, RetrievedChunk


logger = get_logger(__name__)

TOC_LINE_PATTERN = re.compile(r"[\u4e00-\u9fffA-Za-z0-9（）()、/\s]{2,}[\.·…]{3,}\s*\d{1,4}")
PAGE_LIST_PATTERN = re.compile(r"[\u4e00-\u9fffA-Za-z0-9（）()、/]{2,}\s+\d{1,4}$")
DOT_RUN_PATTERN = re.compile(r"[\.·•…]{5,}")
PAGE_REF_PATTERN = re.compile(r"[\.·•…]{5,}\s*\d{1,4}")
TOC_ENTRY_PATTERN = re.compile(
    r"[\u4e00-\u9fffA-Za-z0-9（）()/-]{2,40}\s*[\.·•…]{5,}\s*\d{1,4}"
)
FIGURE_LEGEND_PATTERN = re.compile(r"^\s*(?:\d{2}|0\d|[①②③④⑤⑥⑦⑧⑨⑩])[\s：:、-]+")
GENERIC_NOTICE_TEXTS = {
    "注意事项",
    "注意事项：",
    "警告",
    "警告！",
    "注意",
    "注意！",
    "说明",
    "说明！",
}
GENERIC_PREFACE_PHRASES = {
    "在使用车辆时，请时刻遵循以下注意事项",
    "在使用车辆时，请时刻遵循以下注意事项。",
}
SAFETY_MARKERS = {"警告！", "警告:", "警告：", "禁止", "不得", "切勿", "生命危险", "人身伤害"}
ACTION_MARKERS = {
    "按下",
    "拉出",
    "插入",
    "转动",
    "检查",
    "启用",
    "关闭",
    "打开",
    "调节",
    "锁扣",
    "锁舌",
}
ENTITY_MARKERS = {
    "安全带",
    "胎压",
    "涉水",
    "充电",
    "充电枪",
    "充电口",
    "儿童锁",
    "制动",
    "高压",
    "气囊",
    "警告灯",
    "锁扣",
    "锁舌",
}


def is_toc_chunk(chunk_or_item: Chunk | RetrievedChunk) -> tuple[bool, str | None]:
    chunk = _as_chunk(chunk_or_item)
    text = _compact_text(chunk.text)
    if not text:
        return False, None

    dotted_count = len(re.findall(r"[\.·…]{4,}", chunk.text))
    toc_line_count = sum(1 for line in chunk.text.splitlines() if TOC_LINE_PATTERN.search(line))
    page_list_count = sum(1 for line in chunk.text.splitlines() if PAGE_LIST_PATTERN.search(line.strip()))
    has_toc_heading = "目录" in text[:80] or chunk.chapter == "目录" or chunk.section == "目录"
    has_no_heading = not chunk.chapter and not chunk.section
    dot_run_count = len(DOT_RUN_PATTERN.findall(chunk.text))
    page_ref_count = len(PAGE_REF_PATTERN.findall(chunk.text))
    toc_entry_count = len(TOC_ENTRY_PATTERN.findall(chunk.text))

    # TOC fragments can survive without the word "目录"; require multiple page refs
    # so ordinary ellipses in正文 are not treated as table-of-contents content.
    if has_no_heading and toc_entry_count >= 2:
        return True, "toc_dotted_fragment"
    if has_no_heading and dot_run_count >= 2 and page_ref_count >= 2:
        return True, "toc_page_refs"

    if toc_line_count >= 3 or dotted_count >= 6:
        return True, "toc_dotted_lines"
    if has_toc_heading and (toc_line_count >= 1 or page_list_count >= 5 or dotted_count >= 2):
        return True, "toc_heading"
    if not chunk.chapter and not chunk.section and page_list_count >= 8:
        return True, "toc_page_number_list"
    return False, None


def is_noise_chunk(chunk_or_item: Chunk | RetrievedChunk) -> tuple[bool, str | None]:
    chunk = _as_chunk(chunk_or_item)
    text = _compact_text(chunk.text)
    if not text:
        return True, "empty_text"

    if _contains_real_safety_or_action(text):
        return False, None

    text_length = len(text)
    chapter = chunk.chapter or ""
    if chapter == "前言" and text in GENERIC_NOTICE_TEXTS:
        return True, "generic_preface_notice"
    if chapter == "前言" and any(phrase in text for phrase in GENERIC_PREFACE_PHRASES):
        return True, "generic_preface_notice"
    if (
        chapter == "前言"
        and any(term in text for term in ("警告", "注意", "说明"))
        and any(term in text for term in ("表示", "含义", "用于"))
        and not _contains_entity(text)
    ):
        return True, "generic_preface_notice"

    if text_length <= 16 and text.rstrip("：:。") in {item.rstrip("：:。") for item in GENERIC_NOTICE_TEXTS}:
        return True, "too_short_generic_notice"

    if text_length <= 28 and not _contains_entity(text) and any(term in text for term in ("注意事项", "说明", "警告", "注意")):
        return True, "too_short_generic_notice"

    lines = [line.strip() for line in chunk.text.splitlines() if line.strip()]
    if lines and len(lines) <= 8:
        figure_lines = sum(1 for line in lines if FIGURE_LEGEND_PATTERN.match(line))
        if figure_lines >= max(2, len(lines) - 1) and not _contains_action(text):
            return True, "figure_legend_only"

    return False, None


def filter_retrieval_chunks(
    chunks: list[RetrievedChunk],
    *,
    stage: str,
    remove_toc: bool = True,
    remove_noise: bool = True,
) -> tuple[list[RetrievedChunk], dict[str, Any]]:
    kept: list[RetrievedChunk] = []
    reason_counts: Counter[str] = Counter()
    removed_toc_count = 0
    removed_noise_count = 0

    for item in chunks:
        filtered, reason, is_toc, is_noise = _filter_reason(item.chunk, remove_toc, remove_noise)
        if filtered:
            reason_counts[reason or "unknown"] += 1
            removed_toc_count += int(is_toc)
            removed_noise_count += int(is_noise and not is_toc)
            continue
        kept.append(_with_filter_metadata(item, is_toc=is_toc, is_noise=is_noise, reason=reason))

    summary = {
        "stage": stage,
        "before_filter_count": len(chunks),
        "after_filter_count": len(kept),
        "removed_toc_count": removed_toc_count,
        "removed_noise_count": removed_noise_count,
        "filter_reason_counts": dict(reason_counts),
    }
    logger.info("Retrieval chunk filter completed: stage=%s summary=%s", stage, summary)
    return kept, summary


def filter_index_chunks(
    chunks: list[Chunk],
    *,
    stage: str = "bm25_build",
    remove_toc: bool = True,
    remove_noise: bool = True,
) -> tuple[list[Chunk], dict[str, Any]]:
    kept: list[Chunk] = []
    reason_counts: Counter[str] = Counter()
    removed_toc_count = 0
    removed_noise_count = 0

    for chunk in chunks:
        filtered, reason, is_toc, is_noise = _filter_reason(chunk, remove_toc, remove_noise)
        if filtered:
            reason_counts[reason or "unknown"] += 1
            removed_toc_count += int(is_toc)
            removed_noise_count += int(is_noise and not is_toc)
            continue
        kept.append(
            chunk.model_copy(
                update={
                    "metadata": {
                        **chunk.metadata,
                        "is_toc": is_toc,
                        "is_noise": is_noise,
                        "filter_reason": reason or "",
                    }
                }
            )
        )

    summary = {
        "stage": stage,
        "raw_chunk_count": len(chunks),
        "indexed_chunk_count": len(kept),
        "filtered_chunk_count": len(chunks) - len(kept),
        "bm25_indexed_chunk_count": len(kept),
        "bm25_filtered_chunk_count": len(chunks) - len(kept),
        "removed_toc_count": removed_toc_count,
        "removed_noise_count": removed_noise_count,
        "filter_reason_counts": dict(reason_counts),
    }
    logger.info("Index chunk filter completed: stage=%s summary=%s", stage, summary)
    return kept, summary


def inspect_chunk_filter(chunk: Chunk, stage: str = "inspect_chunks") -> dict[str, Any]:
    toc, toc_reason = is_toc_chunk(chunk)
    noise, noise_reason = is_noise_chunk(chunk)
    return {
        "stage": stage,
        "is_toc": toc,
        "is_noise": noise,
        "filter_reason": toc_reason or noise_reason or "",
    }


def deduplicate_chunks_by_content(
    chunks: list[RetrievedChunk],
    *,
    stage: str,
    min_length: int = 30,
) -> tuple[list[RetrievedChunk], dict[str, Any]]:
    best_by_key: dict[str, tuple[int, RetrievedChunk]] = {}
    original_keys: list[str] = []
    duplicate_keys: set[str] = set()
    chunk_id_duplicates = 0

    for index, item in enumerate(chunks):
        text_key = normalize_text_for_dedup(item.chunk.text)
        if len(text_key) < min_length:
            key = f"chunk:{item.chunk.chunk_id}"
        else:
            key = f"text:{text_key}"

        if key not in best_by_key:
            best_by_key[key] = (index, item)
            original_keys.append(key)
            continue

        duplicate_keys.add(key)
        existing_index, existing_item = best_by_key[key]
        if _dedup_priority(item) > _dedup_priority(existing_item):
            best_by_key[key] = (existing_index, item)

    seen_chunk_ids: set[str] = set()
    deduped: list[RetrievedChunk] = []
    for key in original_keys:
        _, item = best_by_key[key]
        if item.chunk.chunk_id in seen_chunk_ids:
            chunk_id_duplicates += 1
            duplicate_keys.add(f"chunk:{item.chunk.chunk_id}")
            continue
        seen_chunk_ids.add(item.chunk.chunk_id)
        deduped.append(item)

    removed = len(chunks) - len(deduped)
    summary = {
        "stage": stage,
        "before_dedup_count": len(chunks),
        "after_dedup_count": len(deduped),
        "duplicate_removed_count": removed,
        "duplicate_groups_count": len(duplicate_keys),
    }
    logger.info("Content dedup completed: stage=%s summary=%s", stage, summary)
    return deduped, summary


def normalize_text_for_dedup(text: str) -> str:
    normalized = re.sub(r"[\s\n\r\t]+", "", text)
    normalized = re.sub(r"^\d{1,4}", "", normalized)
    normalized = re.sub(r"\d{1,4}$", "", normalized)
    normalized = re.sub(r"[■•\-①②③④⑤⑥⑦⑧⑨⑩]", "", normalized)
    normalized = re.sub(r"（\d+）|\d+\.", "", normalized)
    normalized = re.sub(r"[，,。；;：:！？!?.、（）()\[\]【】《》\"'“”‘’]+", "", normalized)
    return normalized


def _filter_reason(
    chunk: Chunk,
    remove_toc: bool,
    remove_noise: bool,
) -> tuple[bool, str | None, bool, bool]:
    is_toc, toc_reason = is_toc_chunk(chunk)
    if is_toc and remove_toc:
        return True, toc_reason, True, False
    is_noise, noise_reason = is_noise_chunk(chunk)
    if is_noise and remove_noise:
        return True, noise_reason, False, True
    return False, toc_reason or noise_reason, is_toc, is_noise


def _with_filter_metadata(
    item: RetrievedChunk,
    *,
    is_toc: bool,
    is_noise: bool,
    reason: str | None,
) -> RetrievedChunk:
    return item.model_copy(
        update={
            "chunk": item.chunk.model_copy(
                update={
                    "metadata": {
                        **item.chunk.metadata,
                        "is_toc": is_toc,
                        "is_noise": is_noise,
                        "filter_reason": reason or "",
                    }
                }
            )
        }
    )


def _as_chunk(chunk_or_item: Chunk | RetrievedChunk) -> Chunk:
    return chunk_or_item.chunk if isinstance(chunk_or_item, RetrievedChunk) else chunk_or_item


def _compact_text(text: str) -> str:
    return re.sub(r"\s+", "", text.strip())


def _contains_real_safety_or_action(text: str) -> bool:
    return any(marker in text for marker in SAFETY_MARKERS) or (
        _contains_entity(text) and _contains_action(text)
    )


def _contains_entity(text: str) -> bool:
    return any(marker in text for marker in ENTITY_MARKERS)


def _contains_action(text: str) -> bool:
    return any(marker in text for marker in ACTION_MARKERS)


def _dedup_priority(item: RetrievedChunk) -> tuple[int, int, float, int, int]:
    chunk = item.chunk
    metadata_score = sum(1 for value in chunk.metadata.values() if value not in (None, ""))
    ranking_score = item.selection_score
    if ranking_score is None:
        ranking_score = item.score
    if ranking_score is None:
        ranking_score = 0.0
    return (
        int(bool(chunk.section)),
        int(bool(chunk.chapter)),
        float(ranking_score),
        len(chunk.text),
        metadata_score,
    )
