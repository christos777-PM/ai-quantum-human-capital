"""Compare two independent skill-annotation JSONL files.

Reports set-level agreement for multi-label annotations. This measures
consistency between annotation files; it does not establish correctness,
independence, or adjudication quality.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

try:
    from .evaluate_benchmark import load_jsonl
except ImportError:  # Support direct execution as a script.
    from evaluate_benchmark import load_jsonl


def _index_annotations(
    records: Iterable[dict[str, Any]], annotator_name: str
) -> dict[str, tuple[str, set[str]]]:
    """Index role IDs to normalized skill sets, rejecting ambiguous records."""
    indexed: dict[str, tuple[str, set[str]]] = {}
    for index, record in enumerate(records, start=1):
        role_id = record.get("role_id")
        if not isinstance(role_id, str) or not role_id.strip():
            raise ValueError(
                f"{annotator_name} record {index} must have a non-empty role_id."
            )
        display_id = role_id.strip()
        key = display_id.casefold()
        if key in indexed:
            raise ValueError(
                f"{annotator_name} contains duplicate role_id: {display_id!r}."
            )

        skills = record.get("gold_skills")
        if not isinstance(skills, list) or any(
            not isinstance(skill, str) or not skill.strip() for skill in skills
        ):
            raise ValueError(
                f"{annotator_name} record {display_id!r} must contain a "
                "'gold_skills' list of non-empty strings."
            )
        normalized_skills = {skill.strip().casefold() for skill in skills}
        if len(normalized_skills) != len(skills):
            raise ValueError(
                f"{annotator_name} record {display_id!r} contains duplicate "
                "gold_skills after case/whitespace normalization."
            )
        indexed[key] = (display_id, normalized_skills)

    if not indexed:
        raise ValueError(f"{annotator_name} contains no annotation records.")
    return indexed


def compare_annotations(
    annotator_a_records: Iterable[dict[str, Any]],
    annotator_b_records: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Compare two annotation files using exact canonical-label set agreement.

    Role IDs are matched after trimming and case-folding. Skill labels are
    matched after trimming and case-folding; no synonym inference is attempted.
    """
    annotator_a = _index_annotations(annotator_a_records, "Annotator A")
    annotator_b = _index_annotations(annotator_b_records, "Annotator B")

    missing_from_b = sorted(
        annotator_a[key][0] for key in set(annotator_a) - set(annotator_b)
    )
    missing_from_a = sorted(
        annotator_b[key][0] for key in set(annotator_b) - set(annotator_a)
    )
    if missing_from_a or missing_from_b:
        details = []
        if missing_from_b:
            details.append(f"missing from Annotator B: {missing_from_b}")
        if missing_from_a:
            details.append(f"missing from Annotator A: {missing_from_a}")
        raise ValueError("role_id mismatch; " + "; ".join(details) + ".")

    per_role = []
    exact_matches = 0
    jaccard_sum = 0.0
    total_intersection = 0
    total_union = 0

    for key in sorted(annotator_a):
        role_id, skills_a = annotator_a[key]
        _, skills_b = annotator_b[key]
        intersection = skills_a & skills_b
        union = skills_a | skills_b
        exact_match = skills_a == skills_b
        # An empty/empty pair is full agreement, not an undefined score.
        jaccard = len(intersection) / len(union) if union else 1.0

        exact_matches += int(exact_match)
        jaccard_sum += jaccard
        total_intersection += len(intersection)
        total_union += len(union)
        per_role.append(
            {
                "role_id": role_id,
                "exact_match": exact_match,
                "shared_skills": sorted(intersection),
                "only_annotator_a": sorted(skills_a - skills_b),
                "only_annotator_b": sorted(skills_b - skills_a),
                "jaccard": round(jaccard, 4),
            }
        )

    record_count = len(per_role)
    return {
        "records_compared": record_count,
        "exact_set_matches": exact_matches,
        "exact_set_agreement": round(exact_matches / record_count, 4),
        "mean_role_jaccard": round(jaccard_sum / record_count, 4),
        "micro_jaccard": round(
            total_intersection / total_union if total_union else 1.0, 4
        ),
        "per_role": per_role,
        "metric_notes": {
            "normalization": (
                "Role IDs and skill labels are trimmed and case-folded; "
                "skill matching is exact and does not infer synonyms."
            ),
            "jaccard": (
                "Intersection divided by union per role; if both annotators "
                "assign no skills, Jaccard is defined as 1.0."
            ),
            "interpretation": (
                "Pairwise consistency only. This report does not establish "
                "semantic correctness, annotator independence, or adjudication quality."
            ),
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Report pairwise agreement between two skill annotation JSONL files."
    )
    parser.add_argument("--annotator-a", required=True, help="JSONL with role_id and gold_skills")
    parser.add_argument("--annotator-b", required=True, help="JSONL with role_id and gold_skills")
    parser.add_argument("--output", help="Optional path for a JSON report")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = compare_annotations(
            load_jsonl(args.annotator_a),
            load_jsonl(args.annotator_b),
        )
    except (OSError, ValueError) as exc:
        print(f"Annotation agreement error: {exc}", file=sys.stderr)
        return 2

    rendered = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
