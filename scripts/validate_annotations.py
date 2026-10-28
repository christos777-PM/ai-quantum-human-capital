"""Validate evidence links in human-reviewed skill annotation JSONL.

This checks record structure and whether each canonical label has a quote
present in the supplied description. It cannot establish that the label is
semantically correct or that an annotator/reviewer acted independently.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from typing import Any, Iterable

try:
    from .evaluate_benchmark import load_jsonl
except ImportError:  # Support direct execution as a script.
    from evaluate_benchmark import load_jsonl


_VALID_STATUSES = {"draft", "reviewed", "adjudicated"}


def _normalize_text(value: str) -> str:
    """Normalize case and whitespace for quote-presence checks."""
    return re.sub(r"\s+", " ", value).strip().casefold()


def validate_annotation_records(
    records: Iterable[dict[str, Any]],
    *,
    require_adjudicated: bool = False,
) -> dict[str, Any]:
    """Validate annotation structure and evidence-quote presence.

    Each record requires role_id, description, gold_skills, and evidence.
    Evidence is a list of {skill, quote} objects. Every gold label must have
    at least one quote that appears in the description after case/whitespace
    normalization. Empty gold_skills is allowed when evidence is empty.
    """
    seen_ids: set[str] = set()
    status_counts: Counter[str] = Counter()
    total_labels = 0
    record_count = 0

    for index, record in enumerate(records, start=1):
        record_count += 1
        role_id = record.get("role_id")
        if not isinstance(role_id, str) or not role_id.strip():
            raise ValueError(f"Annotation record {index} must have a non-empty role_id.")
        role_id = role_id.strip()
        if role_id in seen_ids:
            raise ValueError(f"Annotations contain duplicate role_id: {role_id!r}.")
        seen_ids.add(role_id)

        description = record.get("description")
        if not isinstance(description, str) or not description.strip():
            raise ValueError(f"Annotation record {role_id!r} must have a non-empty description.")

        skills = record.get("gold_skills")
        if not isinstance(skills, list) or any(
            not isinstance(skill, str) or not skill.strip() for skill in skills
        ):
            raise ValueError(
                f"Annotation record {role_id!r} must contain a gold_skills list "
                "of non-empty strings."
            )
        normalized_skills = [skill.strip().casefold() for skill in skills]
        if len(normalized_skills) != len(set(normalized_skills)):
            raise ValueError(f"Annotation record {role_id!r} contains duplicate gold_skills.")

        evidence = record.get("evidence")
        if not isinstance(evidence, list):
            raise ValueError(f"Annotation record {role_id!r} must contain an evidence list.")

        description_normalized = _normalize_text(description)
        evidence_by_skill: dict[str, list[str]] = {}
        for evidence_index, item in enumerate(evidence, start=1):
            if not isinstance(item, dict):
                raise ValueError(
                    f"Annotation record {role_id!r} evidence item {evidence_index} must be an object."
                )
            skill = item.get("skill")
            quote = item.get("quote")
            if not isinstance(skill, str) or not skill.strip():
                raise ValueError(
                    f"Annotation record {role_id!r} evidence item {evidence_index} "
                    "must have a non-empty skill."
                )
            if not isinstance(quote, str) or not quote.strip():
                raise ValueError(
                    f"Annotation record {role_id!r} evidence item {evidence_index} "
                    "must have a non-empty quote."
                )

            skill_key = skill.strip().casefold()
            if skill_key not in normalized_skills:
                raise ValueError(
                    f"Annotation record {role_id!r} has evidence for unlabelled skill "
                    f"{skill.strip()!r}."
                )
            if _normalize_text(quote) not in description_normalized:
                raise ValueError(
                    f"Annotation record {role_id!r} evidence quote for {skill.strip()!r} "
                    "does not appear in description."
                )
            evidence_by_skill.setdefault(skill_key, []).append(quote.strip())

        missing_evidence = [
            skill.strip()
            for skill, normalized in zip(skills, normalized_skills)
            if normalized not in evidence_by_skill
        ]
        if missing_evidence:
            raise ValueError(
                f"Annotation record {role_id!r} is missing evidence for "
                f"gold_skills {sorted(missing_evidence)}."
            )

        status = record.get("annotation_status", "draft")
        if not isinstance(status, str) or status not in _VALID_STATUSES:
            raise ValueError(
                f"Annotation record {role_id!r} annotation_status must be one of "
                f"{sorted(_VALID_STATUSES)}."
            )
        if require_adjudicated and status != "adjudicated":
            raise ValueError(
                f"Annotation record {role_id!r} has status {status!r}; "
                "release validation requires 'adjudicated'."
            )

        status_counts[status] += 1
        total_labels += len(skills)

    if record_count == 0:
        raise ValueError("Annotation file contains no records.")

    return {
        "records_validated": record_count,
        "skill_labels_validated": total_labels,
        "annotation_status_counts": dict(sorted(status_counts.items())),
        "require_adjudicated": require_adjudicated,
        "validation_scope": (
            "structure, unique role IDs, label/evidence alignment, and quote presence; "
            "not semantic correctness, taxonomy membership, licensing, or reviewer independence"
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate annotation JSONL evidence quotes before benchmark evaluation."
    )
    parser.add_argument("--input", required=True, help="Annotation JSONL file")
    parser.add_argument(
        "--require-adjudicated",
        action="store_true",
        help="Require every record to have annotation_status='adjudicated'.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        report = validate_annotation_records(
            load_jsonl(args.input),
            require_adjudicated=args.require_adjudicated,
        )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
