"""Detect and remove prompt-internal Evidence references from answer text."""

import re


_INTERNAL_REFERENCE_CORE = r"""
(?:
    \[\s*evidence\s+e\d+\s*\]
    | (?<![A-Za-z])evidence(?:\s+id)?\s+e\d+
    | (?<![A-Za-z0-9])e\d+\s+evidence
    | (?<![A-Za-z0-9])e\d+\s*证据
    | 证据\s*e\d+
    | (?:手册片段|资料|片段|上下文|context|source\s+id)\s*\d+
)
"""

INTERNAL_EVIDENCE_REFERENCE_PATTERN = re.compile(
    _INTERNAL_REFERENCE_CORE,
    flags=re.IGNORECASE | re.VERBOSE,
)

_SANITIZABLE_INTERNAL_REFERENCE_PATTERN = re.compile(
    r"""
    (?:(?:根据|参考|参见|参照)\s*)?
    (?:[（(]\s*)?
    """
    + _INTERNAL_REFERENCE_CORE
    + r"""
    (?:\s*[）)])?
    (?:\s*(?:中|里|内))?
    (?:\s*[,，:：]\s*)?
    """,
    flags=re.IGNORECASE | re.VERBOSE,
)


def contains_internal_evidence_reference(text: str) -> bool:
    """Return whether text exposes a prompt-internal Evidence reference."""
    return bool(INTERNAL_EVIDENCE_REFERENCE_PATTERN.search(text))


def strip_internal_evidence_references(text: str) -> str:
    """Remove complete internal references without deleting normal Chinese connectors."""
    cleaned = _SANITIZABLE_INTERNAL_REFERENCE_PATTERN.sub("", text)
    cleaned = re.sub(r"^[\s,，:：;；]+", "", cleaned)
    cleaned = re.sub(r"[（(]\s*[）)]", "", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    return cleaned
