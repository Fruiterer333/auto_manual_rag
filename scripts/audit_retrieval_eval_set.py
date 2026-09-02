import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings
from app.data.schemas.models import Chunk
from app.evaluation.loader import load_eval_cases
from app.evaluation.schemas import EvalCase, EvalEvidence
from app.rag.retrievers.bm25_retriever import BM25Retriever


CLASSIFICATIONS = (
    "UNCHANGED",
    "CHUNK_ID_CHANGED",
    "METADATA_CHANGED",
    "BOUNDARY_CHANGED",
    "MULTI_GOLD_CHANGED",
    "STALE_OR_INVALID",
    "AMBIGUOUS",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit retrieval eval evidence against current indexed chunks."
    )
    parser.add_argument("--dataset", default="data/eval/manual_eval_set.jsonl")
    parser.add_argument(
        "--json-output",
        default="reports/evaluation/v3.5_manual_eval_recalibration_audit.json",
    )
    parser.add_argument(
        "--markdown-output",
        default="reports/evaluation/v3.5_manual_eval_recalibration_audit.md",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cases = load_eval_cases(args.dataset, split="dev")
    retriever = BM25Retriever(get_settings())
    retriever.load_index()
    report = audit_cases(cases, retriever.chunks, dataset_path=args.dataset)
    json_path = Path(args.json_output)
    markdown_path = Path(args.markdown_output)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_path.write_text(format_markdown(report), encoding="utf-8")
    print(f"audit_json={json_path}")
    print(f"audit_markdown={markdown_path}")
    print(f"classification_counts={report['summary']['classification_counts']}")


def audit_cases(
    cases: list[EvalCase],
    chunks: list[Chunk],
    *,
    dataset_path: str,
) -> dict[str, Any]:
    chunks_by_id = {chunk.chunk_id: chunk for chunk in chunks}
    records = [_audit_case(case, chunks, chunks_by_id) for case in cases]
    counts = Counter(record["classification"] for record in records)
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "dataset_path": dataset_path,
        "index_chunk_count": len(chunks),
        "case_count": len(cases),
        "summary": {
            "classification_counts": {
                classification: counts.get(classification, 0)
                for classification in CLASSIFICATIONS
            },
            "requires_manual_review_count": sum(
                record["requires_manual_review"] for record in records
            ),
        },
        "cases": records,
    }


def format_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# V3.5 Manual Eval Recalibration Audit",
        "",
        f"- generated_at: {report['generated_at']}",
        f"- dataset: `{report['dataset_path']}`",
        f"- index_chunk_count: {report['index_chunk_count']}",
        f"- case_count: {report['case_count']}",
        "",
        "## Summary",
        "",
        "| classification | count |",
        "| --- | ---: |",
    ]
    for classification in CLASSIFICATIONS:
        count = report["summary"]["classification_counts"][classification]
        lines.append(f"| {classification} | {count} |")
    lines.extend(
        [
            "",
            f"- requires_manual_review_count: {report['summary']['requires_manual_review_count']}",
            "",
            "## Cases",
            "",
        ]
    )
    for record in report["cases"]:
        lines.extend(
            [
                f"### {record['case_id']}",
                "",
                f"- question: {record['question']}",
                f"- classification: {record['classification']}",
                f"- confidence: {record['confidence']}",
                f"- requires_manual_review: {record['requires_manual_review']}",
                f"- reason: {record['reason']}",
                f"- old_gold_chunk_ids: {_join(record['old_gold_chunk_ids'])}",
                f"- candidate_current_chunk_ids: {_join(record['candidate_current_chunk_ids'])}",
                "",
            ]
        )
        for evidence in record["evidence_audit"]:
            lines.extend(
                [
                    f"#### Evidence {evidence['evidence_index']}",
                    "",
                    f"- old_chunk_id: {evidence['old_chunk_id'] or 'N/A'}",
                    f"- old_page: {evidence['old_page'] if evidence['old_page'] is not None else 'N/A'}",
                    f"- old_section: {evidence['old_section'] or 'N/A'}",
                    f"- old_subsection: {evidence['old_subsection'] or 'N/A'}",
                    f"- old_expected_text: {evidence['old_expected_text'] or 'N/A'}",
                    f"- match_method: {evidence['match_method']}",
                    "",
                ]
            )
            for candidate in evidence["candidates"]:
                lines.extend(
                    [
                        f"- candidate_chunk_id: {candidate['chunk_id']}",
                        f"  - page: {candidate['page']}",
                        f"  - chapter: {candidate['chapter'] or 'N/A'}",
                        f"  - section: {candidate['section'] or 'N/A'}",
                        f"  - subsection: {candidate['subsection'] or 'N/A'}",
                        f"  - heading_path: {_join(candidate['heading_path'], separator=' > ')}",
                        f"  - text: {candidate['text']}",
                    ]
                )
            lines.append("")
    return "\n".join(lines)


def _audit_case(
    case: EvalCase,
    chunks: list[Chunk],
    chunks_by_id: dict[str, Chunk],
) -> dict[str, Any]:
    evidence_audit = [
        _audit_evidence(index, evidence, case, chunks, chunks_by_id)
        for index, evidence in enumerate(case.evidence)
    ]
    classification, reason, confidence, manual_review = _classify_case(evidence_audit)
    candidates = _unique(
        candidate["chunk_id"]
        for evidence in evidence_audit
        for candidate in evidence["candidates"]
    )
    return {
        "case_id": case.id,
        "question": case.question,
        "old_gold_chunk_ids": _unique(
            evidence.chunk_id for evidence in case.evidence if evidence.chunk_id
        ),
        "candidate_current_chunk_ids": candidates,
        "classification": classification,
        "reason": reason,
        "confidence": confidence,
        "requires_manual_review": manual_review,
        "evidence_audit": evidence_audit,
    }


def _audit_evidence(
    evidence_index: int,
    evidence: EvalEvidence,
    case: EvalCase,
    chunks: list[Chunk],
    chunks_by_id: dict[str, Chunk],
) -> dict[str, Any]:
    candidates, method = _find_candidates(evidence, case, chunks, chunks_by_id)
    return {
        "evidence_index": evidence_index,
        "old_chunk_id": evidence.chunk_id,
        "old_expected_text": evidence.quote,
        "old_page": evidence.page,
        "old_chapter": evidence.chapter,
        "old_section": evidence.section,
        "old_subsection": evidence.subsection,
        "old_heading_path": evidence.heading_path,
        "match_method": method,
        "candidates": [_candidate_payload(chunk) for chunk in candidates],
    }


def _find_candidates(
    evidence: EvalEvidence,
    case: EvalCase,
    chunks: list[Chunk],
    chunks_by_id: dict[str, Chunk],
) -> tuple[list[Chunk], str]:
    quote = _normalize(evidence.quote)
    old_chunk = chunks_by_id.get(evidence.chunk_id or "")
    if old_chunk and (not quote or quote in _normalize(old_chunk.text)):
        return [old_chunk], "existing_chunk_id"

    if quote:
        exact = [chunk for chunk in chunks if quote in _normalize(chunk.text)]
        exact = _prefer_expected_page(exact, evidence.page)
        if exact:
            return exact, "exact_quote"

        phrases = _quote_phrases(evidence.quote)
        phrase_matches = [
            chunk
            for chunk in chunks
            if any(phrase in _normalize(chunk.text) for phrase in phrases)
        ]
        phrase_matches = _prefer_expected_page(phrase_matches, evidence.page)
        if phrase_matches:
            return phrase_matches, "quote_phrase"

    page_candidates = [chunk for chunk in chunks if chunk.page == evidence.page]
    anchored = [
        chunk
        for chunk in page_candidates
        if _term_coverage(case.must_contain_terms, chunk.text) >= 0.5
    ]
    return anchored, "page_term_fallback" if anchored else "no_match"


def _classify_case(
    evidence_audit: list[dict[str, Any]],
) -> tuple[str, str, str, bool]:
    if not evidence_audit:
        return "STALE_OR_INVALID", "Case has no gold evidence.", "high", True
    if any(not evidence["candidates"] for evidence in evidence_audit):
        return "AMBIGUOUS", "At least one old evidence item has no reliable current candidate.", "low", True
    if any(len(evidence["candidates"]) > 1 for evidence in evidence_audit):
        return "AMBIGUOUS", "At least one evidence item maps to multiple current candidates.", "medium", True

    old_ids = _unique(
        evidence["old_chunk_id"] for evidence in evidence_audit if evidence["old_chunk_id"]
    )
    new_ids = _unique(evidence["candidates"][0]["chunk_id"] for evidence in evidence_audit)
    metadata_changed = any(_metadata_changed(evidence) for evidence in evidence_audit)
    if old_ids == new_ids and not metadata_changed:
        return "UNCHANGED", "Gold chunk ids and defined metadata still match current chunks.", "high", False
    if len(old_ids) != len(new_ids):
        return "MULTI_GOLD_CHANGED", "The number of unique gold chunks changed.", "high", False
    if metadata_changed:
        return "METADATA_CHANGED", "Direct evidence remains, but current structural metadata changed.", "high", False
    if any(_boundary_changed(evidence) for evidence in evidence_audit):
        return "BOUNDARY_CHANGED", "Direct evidence remains, but the current chunk boundary or heading text changed.", "high", False
    methods = {evidence["match_method"] for evidence in evidence_audit}
    confidence = "high" if methods <= {"existing_chunk_id", "exact_quote"} else "medium"
    return "CHUNK_ID_CHANGED", "Direct evidence maps to a current chunk with a different id.", confidence, confidence != "high"


def _metadata_changed(evidence: dict[str, Any]) -> bool:
    candidate = evidence["candidates"][0]
    comparisons = (
        (evidence["old_page"], candidate["page"]),
        (evidence["old_chapter"], candidate["chapter"]),
        (evidence["old_section"], candidate["section"]),
        (evidence["old_subsection"], candidate["subsection"]),
    )
    return any(expected not in (None, "") and expected != actual for expected, actual in comparisons)


def _boundary_changed(evidence: dict[str, Any]) -> bool:
    candidate = evidence["candidates"][0]
    subsection = candidate["subsection"]
    old_text = _normalize(evidence["old_expected_text"])
    candidate_text = _normalize(candidate["text"])
    heading_added = bool(
        subsection
        and candidate_text.startswith(_normalize(subsection))
        and not old_text.startswith(_normalize(subsection))
    )
    boundary_reduced = bool(
        candidate_text
        and old_text
        and candidate_text in old_text
        and candidate["page"] == evidence["old_page"]
    )
    return heading_added or boundary_reduced


def _candidate_payload(chunk: Chunk) -> dict[str, Any]:
    heading_path = chunk.metadata.get("heading_path")
    if isinstance(heading_path, list):
        normalized_path = [str(item) for item in heading_path]
    else:
        normalized_path = [item for item in (chunk.chapter, chunk.section, chunk.subsection) if item]
    return {
        "chunk_id": chunk.chunk_id,
        "text": chunk.text,
        "page": chunk.page,
        "chapter": chunk.chapter,
        "section": chunk.section,
        "subsection": chunk.subsection,
        "heading_path": normalized_path,
        "content_type": chunk.content_type,
    }


def _prefer_expected_page(chunks: list[Chunk], page: int | None) -> list[Chunk]:
    if page is None:
        return chunks
    same_page = [chunk for chunk in chunks if chunk.page == page]
    return same_page or chunks


def _quote_phrases(text: str) -> list[str]:
    parts = re.split(r"[。；;！!？?\n\r■□]", text)
    return [_normalize(part) for part in parts if len(_normalize(part)) >= 10]


def _term_coverage(terms: list[str], text: str) -> float:
    if not terms:
        return 0.0
    return sum(term in text for term in terms if term) / len(terms)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", "", text)


def _unique(values) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _join(values: list[Any], separator: str = ", ") -> str:
    return separator.join(str(value) for value in values) if values else "N/A"


if __name__ == "__main__":
    main()
