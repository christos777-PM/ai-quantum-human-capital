"""Compare two independent skill-annotation JSONL files.

Reports set-level and per-skill agreement for multi-label annotations.
These measures quantify consistency; they do not establish correctness,
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


def _per_skill_agreement(
    skill: str,
    annotator_a: dict[str, tuple[str, set[str]]],
    annotator_b: dict[str, tuple[str, set[str]]],
) -> dict[str, Any]:
    """Calculate one-vs-rest agreement and Cohen's kappa for one skill."""
    both_present = 0
    only_annotator_a = 0
    only_annotator_b = 0
    both_absent = 0

    for role_id in annotator_a:
        in_a = skill in annotator_a[role_id][1]
        in_b = skill in annotator_b[role_id][1]
        if in_a and in_b:
            both_present += 1
        elif in_a:
            only_annotator_a += 1
        elif in_b:
            only_annotator_b += 1
        else:
            both_absent += 1

    total = both_present + only_annotator_a + only_annotator_b + both_absent
    a_present = both_present + only_annotator_a
    b_present = both_present + only_annotator_b
    a_absent = only_annotator_b + both_absent
    b_absent = only_annotator_a + both_absent

    observed = (both_present + both_absent) / total
    expected = (
        (a_present / total) * (b_present / total)
        + (a_absent / total) * (b_absent / total)
    )
    # Kappa is undefined when expected agreement is 1 (no expected disagreement).
    kappa = None if expected == 1.0 else (observed - expected) / (1 - expected)

    return {
        "skill": skill,
        "both_present": both_present,
        "only_annotator_a": only_annotator_a,
        "only_annotator_b": only_annotator_b,
        "both_absent": both_absent,
        "annotator_a_positive": a_present,
        "annotator_b_positive": b_present,
        "observed_agreement": round(observed, 4),
        "expected_agreement": round(expected, 4),
        "cohen_kappa": round(kappa, 4) if kappa is not None else None,
    }


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

    skill_labels = sorted(
        {skill for _, skills in annotator_a.values() for skill in skills}
        | {skill for _, skills in annotator_b.values() for skill in skills}
    )
    per_skill = [
        _per_skill_agreement(skill, annotator_a, annotator_b)
        for skill in skill_labels
    ]
    defined_kappas = [
        item["cohen_kappa"]
        for item in per_skill
        if item["cohen_kappa"] is not None
    ]

    record_count = len(per_role)
    return {
        "records_compared": record_count,
        "exact_set_matches": exact_matches,
        "exact_set_agreement": round(exact_matches / record_count, 4),
        "mean_role_jaccard": round(jaccard_sum / record_count, 4),
        "micro_jaccard": round(
            total_intersection / total_union if total_union else 1.0, 4
        ),
        "skill_labels_compared": len(per_skill),
        "defined_skill_kappa_count": len(defined_kappas),
        "mean_per_skill_cohen_kappa": (
            round(sum(defined_kappas) / len(defined_kappas), 4)
            if defined_kappas
            else None
        ),
        "per_skill": per_skill,
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
            "cohen_kappa": (
                "One-vs-rest Cohen's kappa is calculated separately for each "
                "observed skill across roles. It is null when expected "
                "agreement is 1.0. The mean is unweighted across defined "
                "skill-level kappas; rare labels and small samples can make "
                "these estimates unstable."
            ),
            "interpretation": (
                "Pairwise consistency only. These statistics do not establish "
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
