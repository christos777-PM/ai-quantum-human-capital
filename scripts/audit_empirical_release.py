"""Run the complete empirical benchmark release preflight in one command."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable

try:
    from .compare_annotations import compare_annotations
    from .evaluate_benchmark import load_jsonl
    from .validate_annotations import load_taxonomy, validate_annotation_records
    from .validate_manifest import validate_manifest
    from .validate_splits import validate_splits
except ImportError:  # Support direct execution as a script.
    from compare_annotations import compare_annotations
    from evaluate_benchmark import load_jsonl
    from validate_annotations import load_taxonomy, validate_annotation_records
    from validate_manifest import validate_manifest
    from validate_splits import validate_splits


def _role_ids(records: Iterable[dict[str, Any]], label: str) -> set[str]:
    ids: set[str] = set()
    for index, record in enumerate(records, start=1):
        role_id = record.get("role_id")
        if not isinstance(role_id, str) or not role_id.strip():
            raise ValueError(f"{label} record {index} must have a non-empty role_id.")
        normalized = role_id.strip().casefold()
        if normalized in ids:
            raise ValueError(f"{label} contains duplicate role_id: {role_id!r}.")
        ids.add(normalized)
    return ids


def audit_empirical_release(
    manifest: dict[str, Any],
    final_annotations: list[dict[str, Any]],
    development_records: list[dict[str, Any]],
    held_out_records: list[dict[str, Any]],
    annotator_a_records: list[dict[str, Any]],
    annotator_b_records: list[dict[str, Any]],
    *,
    taxonomy_path: str | Path,
) -> dict[str, Any]:
    """Combine provenance, annotation, split, and agreement checks.

    A passing report verifies internal consistency only. It cannot establish
    licensing permissions, source authenticity, reviewer independence,
    semantic correctness, or sample representativeness.
    """
    manifest_report = validate_manifest(manifest)
    allowed_skills, taxonomy_version = load_taxonomy(taxonomy_path)
    annotation_report = validate_annotation_records(
        final_annotations,
        require_adjudicated=True,
        allowed_skills=allowed_skills,
        taxonomy_version=taxonomy_version,
    )
    split_report = validate_splits(development_records, held_out_records)
    agreement_report = compare_annotations(annotator_a_records, annotator_b_records)

    for label, records in (
        ("Annotator A", annotator_a_records),
        ("Annotator B", annotator_b_records),
    ):
        for index, record in enumerate(records, start=1):
            skills = record.get("gold_skills")
            if not isinstance(skills, list) or any(
                not isinstance(skill, str) or not skill.strip() for skill in skills
            ):
                raise ValueError(f"{label} record {index} must contain non-empty gold_skills.")
            unknown = sorted(
                {skill.strip().casefold() for skill in skills} - allowed_skills
            )
            if unknown:
                raise ValueError(
                    f"{label} record {index} contains labels outside taxonomy "
                    f"{taxonomy_version}: {unknown}."
                )

    final_ids = _role_ids(final_annotations, "Final annotations")
    development_ids = _role_ids(development_records, "Development split")
    held_out_ids = _role_ids(held_out_records, "Held-out split")
    annotator_a_ids = _role_ids(annotator_a_records, "Annotator A")
    annotator_b_ids = _role_ids(annotator_b_records, "Annotator B")
    split_ids = development_ids | held_out_ids
    counts = manifest["record_counts"]
    double_fraction = manifest["double_annotated_fraction"]
    observed_double_fraction = (
        len(annotator_a_ids) / len(final_ids) if final_ids else 0.0
    )

    checks = {
        "taxonomy_version_matches_manifest": manifest["taxonomy_version"] == taxonomy_version,
        "final_annotations_match_split_ids": final_ids == split_ids,
        "development_count_matches_manifest": len(development_ids) == counts["development"],
        "held_out_count_matches_manifest": len(held_out_ids) == counts["held_out"],
        "included_count_matches_final_annotations": len(final_ids) == counts["included"],
        "annotator_ids_are_subset_of_final_annotations": (
            annotator_a_ids <= final_ids and annotator_b_ids <= final_ids
        ),
        "annotator_files_cover_same_records": annotator_a_ids == annotator_b_ids,
        "double_annotation_fraction_matches_manifest": (
            isinstance(double_fraction, (int, float))
            and not isinstance(double_fraction, bool)
            and math.isclose(
                observed_double_fraction,
                double_fraction,
                rel_tol=0.0,
                abs_tol=1e-6,
            )
        ),
        "split_integrity_passed": split_report["passed"],
    }
    blockers = list(manifest_report["release_blockers"])
    blockers.extend(
        f"{name} failed." for name, passed in checks.items() if not passed
    )
    release_ready = manifest_report["release_ready"] and all(checks.values())

    return {
        "release_ready": release_ready,
        "dataset_id": manifest_report["dataset_id"],
        "version": manifest_report["version"],
        "manifest": manifest_report,
        "annotations": annotation_report,
        "splits": split_report,
        "agreement": agreement_report,
        "checks": checks,
        "observed_double_annotated_fraction": round(observed_double_fraction, 6),
        "release_blockers": blockers,
        "limitations": [
            "This audit checks declared metadata and cross-file consistency, not whether a source license permits the intended use.",
            "It does not independently verify source hashes, annotator independence, semantic correctness, or adjudication quality.",
            "Exact-text split checks do not detect paraphrases or semantic near-duplicates.",
            "Agreement statistics are descriptive and may be unstable for small samples or rare skills.",
            "A passing audit does not establish that the sample represents the Indian technology workforce.",
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the complete empirical benchmark release preflight."
    )
    parser.add_argument("--manifest", required=True, help="Dataset provenance manifest JSON")
    parser.add_argument("--annotations", required=True, help="Final adjudicated annotation JSONL")
    parser.add_argument("--development", required=True, help="Development split JSONL")
    parser.add_argument("--held-out", required=True, help="Held-out split JSONL")
    parser.add_argument("--annotator-a", required=True, help="Pre-adjudication Annotator A JSONL")
    parser.add_argument("--annotator-b", required=True, help="Pre-adjudication Annotator B JSONL")
    parser.add_argument("--taxonomy", required=True, help="Versioned taxonomy snapshot JSON")
    parser.add_argument("--output", help="Optional JSON report output path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        report = audit_empirical_release(
            manifest,
            load_jsonl(args.annotations),
            load_jsonl(args.development),
            load_jsonl(args.held_out),
            load_jsonl(args.annotator_a),
            load_jsonl(args.annotator_b),
            taxonomy_path=args.taxonomy,
        )
    except (OSError, json.JSONDecodeError, ValueError, KeyError) as exc:
        print(f"Empirical release audit error: {exc}", file=sys.stderr)
        return 2

    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report["release_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
