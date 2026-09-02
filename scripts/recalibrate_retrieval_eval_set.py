import argparse
import json
import re
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply high-confidence retrieval benchmark audit mappings."
    )
    parser.add_argument("--dataset", default="data/eval/manual_eval_set.jsonl")
    parser.add_argument(
        "--audit",
        default="reports/evaluation/v3.5_manual_eval_recalibration_audit.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset_path = Path(args.dataset)
    audit = json.loads(Path(args.audit).read_text(encoding="utf-8"))
    audit_by_id = {record["case_id"]: record for record in audit["cases"]}

    updated_cases = 0
    skipped_cases: list[str] = []
    output_lines: list[str] = []
    for line_number, line in enumerate(
        dataset_path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        payload = json.loads(line)
        record = audit_by_id.get(payload["id"])
        if record is None:
            raise ValueError(f"Audit record missing for case at line {line_number}: {payload['id']}")
        if record["requires_manual_review"]:
            skipped_cases.append(payload["id"])
        else:
            _apply_case_mapping(payload, record)
            updated_cases += 1
        output_lines.append(json.dumps(payload, ensure_ascii=False))

    dataset_path.write_text("\n".join(output_lines) + "\n", encoding="utf-8")
    print(f"updated_cases={updated_cases}")
    print(f"manual_review_cases={len(skipped_cases)}")
    print(f"manual_review_case_ids={','.join(skipped_cases) or 'none'}")


def _apply_case_mapping(payload: dict[str, Any], record: dict[str, Any]) -> None:
    evidence_items = payload.get("evidence", [])
    audits = record["evidence_audit"]
    if len(evidence_items) != len(audits):
        raise ValueError(
            f"Evidence count changed after audit for case {payload['id']}: "
            f"dataset={len(evidence_items)} audit={len(audits)}"
        )

    for evidence, evidence_audit in zip(evidence_items, audits, strict=True):
        candidates = evidence_audit["candidates"]
        if len(candidates) != 1:
            raise ValueError(
                f"High-confidence case {payload['id']} has {len(candidates)} candidates."
            )
        candidate = candidates[0]
        old_quote = str(evidence.get("quote") or "")
        current_text = str(candidate["text"])
        if old_quote and _normalize(old_quote) in _normalize(current_text):
            quote = old_quote
        else:
            quote = current_text
        evidence.update(
            {
                "page": candidate["page"],
                "chapter": candidate["chapter"],
                "section": candidate["section"],
                "subsection": candidate["subsection"],
                "heading_path": candidate["heading_path"],
                "chunk_id": candidate["chunk_id"],
                "quote": quote,
            }
        )


def _normalize(text: str) -> str:
    return re.sub(r"\s+", "", text)


if __name__ == "__main__":
    main()
