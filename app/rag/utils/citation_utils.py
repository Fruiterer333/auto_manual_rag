import re


COMMON_TERMS = [
    "涉水驾驶",
    "胎压报警",
    "安全带",
    "儿童锁",
    "充电安全",
    "高压系统",
    "制动系统",
    "转向助力",
    "外部车灯",
]

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

ACTION_TERMS = {"检查", "注意", "警告", "禁止", "必须", "应", "请"}
LEADING_TERMS = {"如下", "下列", "以下", "检查", "注意"}
LIST_ITEM_PATTERN = re.compile(r"^\s*(?:■|-|•|\d+\.|（\d+）|[①②③④⑤⑥⑦⑧⑨⑩])")


def build_relevant_quote(question: str, text: str, max_length: int = 220) -> str:
    if max_length <= 0:
        return ""

    normalized_text = _normalize_whitespace(text)
    if not normalized_text:
        return ""

    keywords = _extract_keywords(question)
    segments = _split_segments(normalized_text)
    if not segments:
        return _trim_quote(normalized_text, max_length)

    scored_segments = [
        (_score_segment(segment, question, keywords), index)
        for index, segment in enumerate(segments)
    ]
    best_score, best_index = max(scored_segments, key=lambda item: item[0])
    if best_score <= 0:
        return _trim_quote(normalized_text, max_length)

    quote = _build_context_quote(segments, best_index, max_length)
    return _trim_quote(quote, max_length)


def _extract_keywords(question: str) -> list[str]:
    keywords: list[str] = []
    for term in COMMON_TERMS:
        if term in question:
            keywords.append(term)

    tokens = re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z0-9]{2,}", question)
    for token in tokens:
        if token in STOPWORDS:
            continue
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


def _split_segments(text: str) -> list[str]:
    normalized = text.replace("\r", "\n")
    parts = re.split(r"(?<=[。；！？])|\n+", normalized)
    return [_normalize_whitespace(part) for part in parts if _normalize_whitespace(part)]


def _score_segment(segment: str, question: str, keywords: list[str]) -> float:
    if len(segment) < 4:
        return -1.0

    score = 0.0
    for keyword in keywords:
        if keyword in segment:
            score += 2.0 if len(keyword) >= 4 else 1.0

    compact_question = _compact_question(question)
    if compact_question and compact_question in segment:
        score += 4.0

    if any(term in segment for term in ACTION_TERMS):
        score += 0.5

    if len(segment) <= 8 and not any(keyword in segment for keyword in keywords):
        score -= 1.0

    return score


def _build_context_quote(segments: list[str], best_index: int, max_length: int) -> str:
    selected = [segments[best_index]]
    should_merge_forward = _is_leading_segment(segments[best_index])

    next_index = best_index + 1
    while next_index < len(segments):
        next_segment = segments[next_index]
        if not _should_merge_next(next_segment, should_merge_forward):
            break
        candidate = _join_segments(selected + [next_segment])
        if len(candidate) > max_length + 40:
            break
        selected.append(next_segment)
        should_merge_forward = should_merge_forward or _is_list_item(next_segment)
        next_index += 1

    if len(_join_segments(selected)) < max_length * 0.7 and best_index > 0:
        previous = segments[best_index - 1]
        if _is_leading_segment(previous) or _shares_action_context(previous):
            candidate = _join_segments([previous] + selected)
            if len(candidate) <= max_length + 20:
                selected.insert(0, previous)

    return _join_segments(selected)


def _should_merge_next(segment: str, should_merge_forward: bool) -> bool:
    if _is_list_item(segment):
        return True
    if should_merge_forward:
        return _shares_action_context(segment) or _is_leading_segment(segment)
    return False


def _is_leading_segment(segment: str) -> bool:
    return any(term in segment for term in LEADING_TERMS)


def _is_list_item(segment: str) -> bool:
    return bool(LIST_ITEM_PATTERN.match(segment))


def _shares_action_context(segment: str) -> bool:
    return any(term in segment for term in ACTION_TERMS)


def _compact_question(question: str) -> str:
    compact = re.sub(r"\s+", "", question)
    for stopword in STOPWORDS:
        compact = compact.replace(stopword, "")
    return compact if len(compact) >= 4 else ""


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _join_segments(segments: list[str]) -> str:
    return " ".join(segment.strip() for segment in segments if segment.strip())


def _trim_quote(quote: str, max_length: int) -> str:
    normalized = _normalize_whitespace(quote)
    if len(normalized) <= max_length:
        return normalized

    cut = normalized[:max_length]
    for delimiter in ("。", "；", "！", "？"):
        delimiter_index = cut.rfind(delimiter)
        if delimiter_index >= int(max_length * 0.55):
            return cut[: delimiter_index + 1].strip()

    last_space = cut.rfind(" ")
    if last_space >= int(max_length * 0.75):
        return cut[:last_space].strip()
    return cut.strip()
