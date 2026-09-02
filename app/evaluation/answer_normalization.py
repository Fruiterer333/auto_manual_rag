"""Conservative normalization for deterministic Answer Evaluation matching."""

import re
import unicodedata


_PUNCTUATION_PATTERN = re.compile(r"[，,。；;：:！？!?、（）()\[\]【】“”\"'‘’]+")
_CENTIMETER_PATTERN = re.compile(r"(?P<number>\d+(?:\.\d+)?)\s*(?:厘米|cm)(?![a-z])")


def normalize_term_for_match(term: str) -> str:
    """Return the conservative comparison form for a required term."""
    return _normalize_for_match(term)


def normalize_answer_for_match(answer: str) -> str:
    """Return the conservative comparison form for an answer body."""
    return _normalize_for_match(answer)


def term_matches_answer(term: str, answer: str) -> bool:
    """Match a term by deterministic formatting equivalence only."""
    normalized_term = normalize_term_for_match(term)
    if not normalized_term:
        return False
    return normalized_term in normalize_answer_for_match(answer)


def _normalize_for_match(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    normalized = _CENTIMETER_PATTERN.sub(
        lambda match: f"{match.group('number')}cm",
        normalized,
    )
    normalized = _PUNCTUATION_PATTERN.sub("", normalized)
    return re.sub(r"\s+", "", normalized)
