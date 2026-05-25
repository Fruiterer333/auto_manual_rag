import re


def build_relevant_quote(question: str, text: str, max_length: int = 180) -> str:
    if max_length <= 0:
        return ""

    normalized_text = text.strip()
    if not normalized_text:
        return ""

    keywords = _extract_keywords(question)
    sentences = _split_sentences(normalized_text)
    if not sentences:
        return normalized_text[:max_length]

    best_index = _find_best_sentence_index(sentences, keywords)
    if best_index is None:
        return normalized_text[:max_length]

    quote = _join_with_neighbors(sentences, best_index, max_length)
    return quote[:max_length].strip()


def _extract_keywords(question: str) -> list[str]:
    tokens = re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z0-9]{2,}", question)
    keywords: list[str] = []
    for token in tokens:
        if token not in keywords:
            keywords.append(token)

    # Add short overlapping Chinese fragments so simple rules can still match
    # when the user asks with longer phrases than the manual uses.
    for token in list(keywords):
        if re.fullmatch(r"[\u4e00-\u9fff]{4,}", token):
            for index in range(len(token) - 1):
                fragment = token[index : index + 2]
                if fragment not in keywords:
                    keywords.append(fragment)

    return keywords


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[。；！？\n])", text)
    return [part.strip() for part in parts if part.strip()]


def _find_best_sentence_index(sentences: list[str], keywords: list[str]) -> int | None:
    if not keywords:
        return None

    best_index: int | None = None
    best_score = 0
    for index, sentence in enumerate(sentences):
        score = sum(1 for keyword in keywords if keyword in sentence)
        if score > best_score:
            best_score = score
            best_index = index

    return best_index


def _join_with_neighbors(sentences: list[str], best_index: int, max_length: int) -> str:
    selected = [sentences[best_index]]

    previous_index = best_index - 1
    if previous_index >= 0:
        previous = sentences[previous_index]
        if len(previous) + len("".join(selected)) <= max_length:
            selected.insert(0, previous)

    next_index = best_index + 1
    if next_index < len(sentences):
        next_sentence = sentences[next_index]
        if len("".join(selected)) + len(next_sentence) <= max_length:
            selected.append(next_sentence)

    return "".join(selected)
