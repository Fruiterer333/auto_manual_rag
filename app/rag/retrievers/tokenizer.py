import re


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+(?:[A-Za-z0-9&+/-]*[A-Za-z0-9])?")
WEAK_QUERY_TERMS = {
    "如何",
    "怎么",
    "哪些",
    "什么",
    "是否",
    "需要",
    "应该",
    "可以",
    "进行",
    "情况",
    "时候",
    "请",
    "有哪些",
}
CONSERVATIVE_WEAK_TERMS = {"注意", "注意事项", "使用", "操作", "车辆"}
WEAK_QUERY_CHARS = {
    "如",
    "何",
    "怎",
    "么",
    "哪",
    "些",
    "什",
    "需",
    "要",
    "应",
    "该",
    "可",
    "以",
    "进",
    "行",
    "情",
    "况",
    "时",
    "候",
    "请",
    "有",
    "后",
    "前",
    "办",
}
CONSERVATIVE_WEAK_CHARS = {"注", "意", "事", "项", "车", "辆", "使", "用", "操", "作"}
GENERIC_QUERY_TERMS = WEAK_QUERY_TERMS | CONSERVATIVE_WEAK_TERMS | {"事项", "注意事项"}


def tokenize_for_bm25(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text.strip())
    tokens: list[str] = []
    tokens.extend(token.lower() for token in TOKEN_PATTERN.findall(normalized))

    chinese_chars = re.findall(r"[\u4e00-\u9fff]", normalized)
    tokens.extend(chinese_chars)
    tokens.extend(_char_ngrams(chinese_chars, 2))
    tokens.extend(_char_ngrams(chinese_chars, 3))
    tokens.extend(_char_ngrams(chinese_chars, 4))
    tokens.extend(_char_ngrams(chinese_chars, 5))
    return tokens


def tokenize_query_for_bm25(query: str) -> list[str]:
    raw_tokens = tokenize_for_bm25(query)
    filtered_tokens, _ = filter_query_tokens(raw_tokens)
    return filtered_tokens


def filter_query_tokens(tokens: list[str]) -> tuple[list[str], list[str]]:
    if not tokens:
        return [], []

    has_core_signal = any(_is_informative_token(token) for token in tokens)
    filtered: list[str] = []
    removed: list[str] = []
    for token in tokens:
        if token in WEAK_QUERY_TERMS:
            removed.append(token)
            continue
        if token in WEAK_QUERY_CHARS:
            removed.append(token)
            continue
        if has_core_signal and token in CONSERVATIVE_WEAK_TERMS:
            removed.append(token)
            continue
        if has_core_signal and token in CONSERVATIVE_WEAK_CHARS:
            removed.append(token)
            continue
        if (
            has_core_signal
            and any(char in WEAK_QUERY_CHARS or char in CONSERVATIVE_WEAK_CHARS for char in token)
            and token not in {"安全", "报警", "检查", "正确", "驾驶"}
            and _informative_char_count(token) < 3
        ):
            removed.append(token)
            continue
        filtered.append(token)

    if not filtered or len(filtered) < 2:
        return tokens, []
    return filtered, removed


def extract_coverage_terms(query: str, filtered_tokens: list[str] | None = None) -> list[str]:
    tokens = filtered_tokens if filtered_tokens is not None else tokenize_query_for_bm25(query)
    candidates: list[str] = []
    for token in tokens:
        token = _normalize_coverage_token(token)
        if len(token) < 2:
            continue
        if len(token) > 4:
            continue
        if token in GENERIC_QUERY_TERMS:
            continue
        if not re.fullmatch(r"[\u4e00-\u9fffA-Za-z0-9&+/-]+", token):
            continue
        if not _is_informative_token(token):
            continue
        if token not in candidates:
            candidates.append(token)

    candidates.sort(
        key=lambda token: (
            min(len(token), 5),
            _informative_char_count(token),
        ),
        reverse=True,
    )
    selected: list[str] = []
    for token in candidates:
        if any(token in existing and len(token) < len(existing) for existing in selected):
            continue
        selected.append(token)
        if len(selected) >= 8:
            break
    return selected


def extract_core_terms(query: str) -> list[str]:
    """Backward-compatible alias; BM25 now uses dynamic coverage terms."""
    return extract_coverage_terms(query)


def _char_ngrams(chars: list[str], n: int) -> list[str]:
    if len(chars) < n:
        return []
    return ["".join(chars[index : index + n]) for index in range(len(chars) - n + 1)]


def _is_informative_token(token: str) -> bool:
    if token in GENERIC_QUERY_TERMS:
        return False
    if len(token) >= 2 and re.fullmatch(r"[A-Za-z0-9&+/-]+", token):
        return True
    return _informative_char_count(token) >= 2


def _informative_char_count(token: str) -> int:
    return sum(
        1
        for char in token
        if char not in WEAK_QUERY_CHARS and char not in CONSERVATIVE_WEAK_CHARS
    )


def _normalize_coverage_token(token: str) -> str:
    weak_chars = WEAK_QUERY_CHARS | CONSERVATIVE_WEAK_CHARS
    start = 0
    end = len(token)
    while end - start > 2 and token[start] in weak_chars:
        start += 1
    while end - start > 2 and token[end - 1] in weak_chars:
        end -= 1
    return token[start:end]
