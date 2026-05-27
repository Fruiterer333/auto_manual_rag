import re

from app.core.logger import get_logger
from app.data.schemas.models import RetrievedChunk


logger = get_logger(__name__)


STOPWORDS = {
    "如何",
    "怎么",
    "什么",
    "哪些",
    "需要",
    "应该",
    "可以",
    "车辆",
    "使用",
    "进行",
    "之后",
    "如果",
    "是否",
    "的",
    "了",
    "和",
    "与",
    "在",
    "后",
    "前",
    "时",
}

OPERATION_INTENT_TERMS = {"如何", "怎么", "步骤", "使用", "启用", "打开", "关闭", "检查", "调节", "设置"}
SAFETY_INTENT_TERMS = {"安全", "注意事项", "警告", "禁止", "不得", "风险"}
FAULT_INTENT_TERMS = {"报警", "故障", "警告灯", "指示灯"}
def select_contexts(
    question: str,
    retrieved: list[RetrievedChunk],
    top_k: int = 5,
    enabled: bool = True,
) -> list[RetrievedChunk]:
    if not enabled:
        return retrieved[:top_k]

    keywords = _extract_keywords(question)
    intents = _detect_intents(question)
    scored: list[RetrievedChunk] = []
    for item in retrieved:
        metadata_bonus = _metadata_bonus(item, keywords, intents)
        original_score = item.score if item.score is not None else 0.0
        selection_score = original_score + metadata_bonus
        scored.append(item.model_copy(update={"selection_score": selection_score}))

    selected = sorted(
        scored,
        key=lambda item: item.selection_score if item.selection_score is not None else -999.0,
        reverse=True,
    )[:top_k]

    logger.info(
        "Context selection completed: enabled=%s candidates=%s selected=%s intents=%s",
        enabled,
        len(retrieved),
        len(selected),
        sorted(intents),
    )
    for rank, item in enumerate(selected, start=1):
        chunk = item.chunk
        logger.info(
            "Selected context: rank=%s score=%s selection_score=%s page=%s section=%s content_type=%s risk_level=%s",
            rank,
            item.score,
            item.selection_score,
            chunk.page,
            chunk.section,
            chunk.content_type,
            chunk.risk_level,
        )
    return selected


def deduplicate_contexts(contexts: list[RetrievedChunk]) -> tuple[list[RetrievedChunk], int]:
    ranked = sorted(
        contexts,
        key=lambda item: _ranking_score(item),
        reverse=True,
    )
    seen_chunk_ids: set[str] = set()
    seen_texts: set[str] = set()
    deduped: list[RetrievedChunk] = []
    for item in ranked:
        normalized_text = normalize_text_for_dedup(item.chunk.text)
        if item.chunk.chunk_id in seen_chunk_ids or normalized_text in seen_texts:
            continue
        seen_chunk_ids.add(item.chunk.chunk_id)
        if normalized_text:
            seen_texts.add(normalized_text)
        deduped.append(item)

    removed = len(contexts) - len(deduped)
    logger.info(
        "Context dedup completed: before_dedup_count=%s after_dedup_count=%s removed_duplicate_count=%s",
        len(contexts),
        len(deduped),
        removed,
    )
    return deduped, removed


def expand_neighbor_contexts(
    contexts: list[RetrievedChunk],
    neighbor_lookup,
    enabled: bool = True,
    max_per_chunk: int = 1,
) -> list[RetrievedChunk]:
    if not enabled or max_per_chunk <= 0:
        logger.info("Neighbor expansion skipped: enabled=%s", enabled)
        return contexts

    expanded = list(contexts)
    expanded_ids: list[str] = []
    for item in contexts:
        if not _should_expand(item):
            continue
        neighbors = neighbor_lookup(item.chunk, max_per_chunk)
        for neighbor in neighbors:
            expanded.append(neighbor)
            expanded_ids.append(neighbor.chunk.chunk_id)

    logger.info(
        "Neighbor expansion completed: expansion_enabled=%s expanded_count=%s expanded_chunk_ids=%s",
        enabled,
        len(expanded_ids),
        expanded_ids,
    )
    return expanded


def enforce_max_context_chars(
    contexts: list[RetrievedChunk],
    max_chars: int,
) -> list[RetrievedChunk]:
    if max_chars <= 0:
        return contexts

    selected: list[RetrievedChunk] = []
    total_chars = 0
    for item in contexts:
        text_length = len(item.chunk.text)
        if selected and total_chars + text_length > max_chars:
            break
        selected.append(item)
        total_chars += text_length

    logger.info(
        "Context char limit applied: final_context_count=%s final_context_chars=%s max_context_chars=%s",
        len(selected),
        total_chars,
        max_chars,
    )
    return selected


def _ranking_score(item: RetrievedChunk) -> float:
    if item.selection_score is not None:
        return item.selection_score
    if item.score is not None:
        return item.score
    return -999.0


def normalize_text_for_dedup(text: str) -> str:
    normalized = re.sub(r"[\s\n\r\t]+", "", text)
    normalized = re.sub(r"[■•\-①②③④⑤⑥⑦⑧⑨⑩]", "", normalized)
    normalized = re.sub(r"（\d+）|\d+\.", "", normalized)
    return normalized


def _should_expand(item: RetrievedChunk) -> bool:
    chunk = item.chunk
    if chunk.content_type in {"warning", "caution", "procedure"}:
        return True
    text = chunk.text.strip()
    if text.endswith(("：", ":", "，", "、")):
        return True
    return False


def _extract_keywords(question: str) -> list[str]:
    tokens = re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z0-9]{2,}", question)
    keywords: list[str] = []
    for token in tokens:
        reduced = token
        for stopword in STOPWORDS:
            reduced = reduced.replace(stopword, "")
        if len(reduced) >= 2 and reduced not in keywords:
            keywords.append(reduced)
    for token in list(keywords):
        if re.fullmatch(r"[\u4e00-\u9fff]{4,}", token):
            for index in range(len(token) - 1):
                fragment = token[index : index + 2]
                if fragment not in STOPWORDS and fragment not in keywords:
                    keywords.append(fragment)
    return keywords


def _detect_intents(question: str) -> set[str]:
    intents: set[str] = set()
    if any(term in question for term in OPERATION_INTENT_TERMS):
        intents.add("operation")
    if any(term in question for term in SAFETY_INTENT_TERMS):
        intents.add("safety")
    if any(term in question for term in FAULT_INTENT_TERMS):
        intents.add("fault")
    return intents


def _metadata_bonus(
    item: RetrievedChunk,
    keywords: list[str],
    intents: set[str],
) -> float:
    chunk = item.chunk
    bonus = 0.0
    section = chunk.section or ""
    chapter = chunk.chapter or ""
    text = chunk.text

    section_hits = sum(1 for keyword in keywords if keyword and keyword in section)
    chapter_hits = sum(1 for keyword in keywords if keyword and keyword in chapter)
    text_hits = sum(1 for keyword in keywords if keyword and keyword in text)

    bonus += min(section_hits * 0.05, 0.15)
    bonus += min(chapter_hits * 0.03, 0.06)
    bonus += min(text_hits * 0.015, 0.09)

    if "operation" in intents:
        if chunk.content_type == "procedure":
            bonus += 0.06
        if section_hits or text_hits:
            bonus += 0.04

    if "safety" in intents:
        if chunk.content_type in {"warning", "caution"}:
            bonus += 0.07
        if chunk.risk_level in {"high", "medium"}:
            bonus += 0.04

    if "fault" in intents:
        if any(term in section or term in text for term in FAULT_INTENT_TERMS):
            bonus += 0.06
        if chunk.risk_level in {"medium", "high"}:
            bonus += 0.03

    return min(bonus, 0.25)
