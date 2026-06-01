import re
from collections import Counter, defaultdict
from statistics import mean
from typing import Iterable

from app.data.schemas.models import RetrievedChunk
from app.evaluation.schemas import EvalCase, RetrievalEvalResult, RetrievalHitDetail
from app.rag.retrievers.chunk_filters import inspect_chunk_filter, normalize_text_for_dedup


K_VALUES = (1, 3, 5)


def evaluate_case_retrieval(
    case: EvalCase,
    retrieved: list[RetrievedChunk],
    *,
    retrieval_mode: str,
    top_k: int,
    final_contexts: list[RetrievedChunk] | None = None,
    use_context_selection: bool = False,
) -> RetrievalEvalResult:
    metrics: dict[str, float | int | bool | None] = {}
    max_k = min(top_k, len(retrieved))
    for k in K_VALUES:
        if k > top_k:
            continue
        top_items = retrieved[:k]
        metrics[f"page_hit@{k}"] = _page_hit(case, top_items)
        metrics[f"expected_section_hit@{k}"] = _section_hit(case.expected_sections, top_items)
        metrics[f"acceptable_section_hit@{k}"] = _section_hit(
            case.expected_sections + case.acceptable_sections,
            top_items,
        )
        metrics[f"content_type_hit@{k}"] = _content_type_hit(case, top_items)
        metrics[f"any_term_hit@{k}"] = _any_term_hit(case.must_contain_terms, top_items)
        metrics[f"all_terms_hit@{k}"] = _all_terms_hit(case.must_contain_terms, top_items)
        metrics[f"term_coverage_ratio@{k}"] = _term_coverage_ratio(case.must_contain_terms, top_items)
        metrics[f"evidence_hit@{k}"] = _evidence_hit(case, top_items)
        metrics[f"noise_rate@{k}"] = _noise_rate(top_items)
        duplicate_metrics = _duplicate_metrics(top_items)
        metrics[f"duplicate_chunk_id_rate@{k}"] = duplicate_metrics["duplicate_chunk_id_rate"]
        metrics[f"same_page_duplicate_rate@{k}"] = duplicate_metrics["same_page_duplicate_rate"]
        metrics[f"cross_page_repeated_content_rate@{k}"] = duplicate_metrics[
            "cross_page_repeated_content_rate"
        ]

    first_hit_rank = _first_evidence_hit_rank(case, retrieved[:top_k])
    metrics["first_evidence_hit_rank"] = first_hit_rank
    metrics["mrr"] = 1.0 / first_hit_rank if first_hit_rank else 0.0
    metrics["average_first_hit_rank"] = float(first_hit_rank) if first_hit_rank else None
    metrics["retrieved_count"] = max_k

    if final_contexts is not None:
        metrics["final_context_hit"] = _evidence_hit(case, final_contexts[:top_k])
        metrics["final_context_count"] = len(final_contexts)

    failure_reasons = _failure_reasons(metrics, top_k)
    return RetrievalEvalResult(
        case_id=case.id,
        question=case.question,
        category=case.category,
        intent_type=case.intent_type,
        retrieval_mode=retrieval_mode,
        top_k=top_k,
        use_context_selection=use_context_selection,
        metrics=metrics,
        raw_hits=_hit_details(case, retrieved[:top_k]),
        final_hits=_hit_details(case, final_contexts[:top_k]) if final_contexts else [],
        failure_reasons=failure_reasons,
    )


def aggregate_results(results: list[RetrievalEvalResult]) -> dict[str, float | int | None]:
    if not results:
        return {}
    keys = sorted({key for result in results for key in result.metrics})
    summary: dict[str, float | int | None] = {"case_count": len(results)}
    for key in keys:
        values: list[float] = []
        for result in results:
            value = result.metrics.get(key)
            if isinstance(value, bool):
                values.append(1.0 if value else 0.0)
            elif isinstance(value, (int, float)):
                values.append(float(value))
        if values:
            summary[key] = mean(values)
    return summary


def group_aggregate(
    results: list[RetrievalEvalResult],
    *,
    field: str,
) -> dict[str, dict[str, float | int | None]]:
    grouped: dict[str, list[RetrievalEvalResult]] = defaultdict(list)
    for result in results:
        grouped[str(getattr(result, field))].append(result)
    return {key: aggregate_results(group_results) for key, group_results in grouped.items()}


def _page_hit(case: EvalCase, chunks: list[RetrievedChunk]) -> bool | None:
    if not case.expected_pages:
        return None
    return any(item.chunk.page in case.expected_pages for item in chunks)


def _section_hit(expected_sections: list[str], chunks: list[RetrievedChunk]) -> bool | None:
    if not expected_sections:
        return None
    return any(_matches_any_section(item.chunk.section, expected_sections) for item in chunks)


def _content_type_hit(case: EvalCase, chunks: list[RetrievedChunk]) -> bool | None:
    if not case.expected_content_types:
        return None
    expected = {item.lower() for item in case.expected_content_types}
    return any((item.chunk.content_type or "").lower() in expected for item in chunks)


def _any_term_hit(terms: list[str], chunks: list[RetrievedChunk]) -> bool | None:
    if not terms:
        return None
    text = _joined_text(chunks)
    return any(term and term in text for term in terms)


def _all_terms_hit(terms: list[str], chunks: list[RetrievedChunk]) -> bool | None:
    if not terms:
        return None
    text = _joined_text(chunks)
    return all(term and term in text for term in terms)


def _term_coverage_ratio(terms: list[str], chunks: list[RetrievedChunk]) -> float | None:
    if not terms:
        return None
    text = _joined_text(chunks)
    matched = sum(1 for term in terms if term and term in text)
    return matched / len(terms)


def _evidence_hit(case: EvalCase, chunks: list[RetrievedChunk]) -> bool:
    return any(_is_evidence_hit(case, item) for item in chunks)


def _first_evidence_hit_rank(case: EvalCase, chunks: list[RetrievedChunk]) -> int | None:
    for rank, item in enumerate(chunks, start=1):
        if _is_evidence_hit(case, item):
            return rank
    return None


def _is_evidence_hit(case: EvalCase, item: RetrievedChunk) -> bool:
    chunk = item.chunk
    text = chunk.text
    if _quote_hit(case, text):
        return True
    if _matches_any_section(chunk.section, case.expected_sections) and _any_term_in_text(
        case.must_contain_terms,
        text,
    ):
        return True
    if chunk.page in case.expected_pages and _term_coverage_ratio_for_text(
        case.must_contain_terms,
        text,
    ) >= 0.4:
        return True
    if (
        case.expected_content_types
        and (chunk.content_type or "") in case.expected_content_types
        and _any_term_in_text(case.must_contain_terms, text)
    ):
        return True
    if not case.expected_pages and not case.expected_sections and case.must_contain_terms:
        return _term_coverage_ratio_for_text(case.must_contain_terms, text) >= 0.5
    return False


def _quote_hit(case: EvalCase, text: str) -> bool:
    normalized_text = _normalize_for_match(text)
    for evidence in case.evidence:
        quote = evidence.quote.strip()
        if not quote:
            continue
        normalized_quote = _normalize_for_match(quote)
        if normalized_quote and normalized_quote in normalized_text:
            return True
        for phrase in _quote_key_phrases(quote):
            if _normalize_for_match(phrase) in normalized_text:
                return True
    return False


def _quote_key_phrases(quote: str) -> list[str]:
    parts = re.split(r"[。；;！!？?\n\r■□]", quote)
    return [part.strip() for part in parts if len(_normalize_for_match(part)) >= 8]


def _noise_rate(chunks: list[RetrievedChunk]) -> float:
    if not chunks:
        return 0.0
    noisy = 0
    for item in chunks:
        metadata = item.chunk.metadata
        is_toc = bool(metadata.get("is_toc"))
        is_noise = bool(metadata.get("is_noise"))
        if not is_toc and not is_noise:
            filter_info = inspect_chunk_filter(item.chunk, stage="evaluation_metrics")
            is_toc = bool(filter_info["is_toc"])
            is_noise = bool(filter_info["is_noise"])
        noisy += int(is_toc or is_noise)
    return noisy / len(chunks)


def _duplicate_metrics(chunks: list[RetrievedChunk]) -> dict[str, float]:
    if not chunks:
        return {
            "duplicate_chunk_id_rate": 0.0,
            "same_page_duplicate_rate": 0.0,
            "cross_page_repeated_content_rate": 0.0,
        }
    chunk_ids = [item.chunk.chunk_id for item in chunks]
    duplicate_chunk_ids = _duplicate_count(chunk_ids)

    same_page_keys = [
        (item.chunk.source_file, item.chunk.page, normalize_text_for_dedup(item.chunk.text))
        for item in chunks
    ]
    same_page_duplicates = _duplicate_count(same_page_keys)

    text_pages: dict[str, set[int | None]] = defaultdict(set)
    for item in chunks:
        normalized = normalize_text_for_dedup(item.chunk.text)
        if normalized:
            text_pages[normalized].add(item.chunk.page)
    cross_page_duplicates = sum(
        1
        for item in chunks
        if normalize_text_for_dedup(item.chunk.text)
        and len(text_pages[normalize_text_for_dedup(item.chunk.text)]) > 1
    )

    total = len(chunks)
    return {
        "duplicate_chunk_id_rate": duplicate_chunk_ids / total,
        "same_page_duplicate_rate": same_page_duplicates / total,
        "cross_page_repeated_content_rate": cross_page_duplicates / total,
    }


def _duplicate_count(values: Iterable[object]) -> int:
    counts = Counter(values)
    return sum(count - 1 for count in counts.values() if count > 1)


def _hit_details(case: EvalCase, chunks: list[RetrievedChunk]) -> list[RetrievalHitDetail]:
    details: list[RetrievalHitDetail] = []
    for rank, item in enumerate(chunks, start=1):
        details.append(
            RetrievalHitDetail(
                rank=rank,
                chunk_id=item.chunk.chunk_id,
                page=item.chunk.page,
                section=item.chunk.section,
                score=item.score,
                evidence_hit=_is_evidence_hit(case, item),
            )
        )
    return details


def _failure_reasons(metrics: dict[str, float | int | bool | None], top_k: int) -> list[str]:
    reasons: list[str] = []
    evidence_key = f"evidence_hit@{min(top_k, 5)}"
    if metrics.get(evidence_key) is False:
        reasons.append("no_evidence_hit")
    if (metrics.get(f"noise_rate@{min(top_k, 5)}") or 0) > 0:
        reasons.append("noise_in_top_k")
    if (metrics.get(f"duplicate_chunk_id_rate@{min(top_k, 5)}") or 0) > 0:
        reasons.append("duplicate_chunk_id")
    if (metrics.get(f"same_page_duplicate_rate@{min(top_k, 5)}") or 0) > 0:
        reasons.append("same_page_duplicate")
    return reasons


def _matches_any_section(section: str | None, expected_sections: list[str]) -> bool:
    if not section or not expected_sections:
        return False
    return any(expected in section or section in expected for expected in expected_sections)


def _any_term_in_text(terms: list[str], text: str) -> bool:
    return any(term and term in text for term in terms)


def _term_coverage_ratio_for_text(terms: list[str], text: str) -> float:
    if not terms:
        return 0.0
    return sum(1 for term in terms if term and term in text) / len(terms)


def _joined_text(chunks: list[RetrievedChunk]) -> str:
    return "\n".join(item.chunk.text for item in chunks)


def _normalize_for_match(text: str) -> str:
    return re.sub(r"\s+", "", text)
