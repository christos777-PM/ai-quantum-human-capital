"""Validate benchmark provenance-manifest structure and release metadata."""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


REQUIRED_FIELDS = {
    "dataset_id",
    "version",
    "data_status",
    "source_name",
    "source_url",
    "license_name",
    "license_url",
    "terms_reviewed_at",
    "retrieved_at",
    "collection_method",
    "content_hash_algorithm",
    "source_snapshot_sha256",
    "taxonomy_version",
    "annotation_protocol_version",
    "annotator_count",
    "double_annotated_fraction",
    "agreement_method",
    "adjudication_method",
    "deduplication_method",
    "split_strategy",
    "record_counts",
    "personal_data_review",
    "notes",
}
COUNT_FIELDS = ("collected", "included", "excluded", "development", "held_out")
DATA_STATUSES = {"template", "exploratory", "empirical"}
SHA256_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")
RELEASE_TEXT_FIELDS = (
    "source_name",
    "source_url",
    "license_name",
    "license_url",
    "terms_reviewed_at",
    "retrieved_at",
    "collection_method",
    "source_snapshot_sha256",
    "taxonomy_version",
    "annotation_protocol_version",
    "agreement_method",
    "adjudication_method",
    "deduplication_method",
    "split_strategy",
)


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_url(value: Any, field: str) -> None:
    if value is None:
        return
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a URL string or null.")
    parsed = urlparse(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{field} must be an absolute HTTP(S) URL.")


def _validate_date(value: Any, field: str) -> None:
    if value is None:
        return
    if not isinstance(value, str):
        raise ValueError(f"{field} must use YYYY-MM-DD or be null.")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} must use YYYY-MM-DD.") from exc


def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    """Validate metadata consistency and report fields needed for empirical release.

    A release-ready result means only that declared metadata is complete and
    internally consistent. It does not independently verify licensing, hashes,
    source contents, annotation quality, or reviewer independence.
    """
    if not isinstance(manifest, dict):
        raise ValueError("Manifest must contain a JSON object.")

    missing_fields = sorted(REQUIRED_FIELDS - set(manifest))
    if missing_fields:
        raise ValueError(f"Manifest is missing required fields: {missing_fields}.")

    for field in ("dataset_id", "version"):
        if not _non_empty_string(manifest[field]):
            raise ValueError(f"{field} must be a non-empty string.")

    if manifest["data_status"] not in DATA_STATUSES:
        raise ValueError(f"data_status must be one of {sorted(DATA_STATUSES)}.")
    if manifest["content_hash_algorithm"] != "sha256":
        raise ValueError("content_hash_algorithm must be 'sha256'.")

    text_fields = (
        "source_name",
        "license_name",
        "collection_method",
        "taxonomy_version",
        "annotation_protocol_version",
        "agreement_method",
        "adjudication_method",
        "deduplication_method",
        "split_strategy",
        "personal_data_review",
        "notes",
    )
    for field in text_fields:
        value = manifest[field]
        if value is not None and not isinstance(value, str):
            raise ValueError(f"{field} must be a string or null.")

    for field in ("source_url", "license_url"):
        _validate_url(manifest[field], field)
    for field in ("terms_reviewed_at", "retrieved_at"):
        _validate_date(manifest[field], field)

    source_hash = manifest["source_snapshot_sha256"]
    if source_hash is not None and (
        not isinstance(source_hash, str)
        or not SHA256_PATTERN.fullmatch(source_hash.strip())
    ):
        raise ValueError("source_snapshot_sha256 must be 64 hexadecimal characters or null.")

    annotator_count = manifest["annotator_count"]
    if annotator_count is not None and (
        isinstance(annotator_count, bool)
        or not isinstance(annotator_count, int)
        or annotator_count < 1
    ):
        raise ValueError("annotator_count must be a positive integer or null.")

    double_fraction = manifest["double_annotated_fraction"]
    if double_fraction is not None and (
        isinstance(double_fraction, bool)
        or not isinstance(double_fraction, (int, float))
        or not 0 <= double_fraction <= 1
    ):
        raise ValueError("double_annotated_fraction must be between 0 and 1 or null.")

    counts = manifest["record_counts"]
    if not isinstance(counts, dict):
        raise ValueError("record_counts must be a JSON object.")
    missing_counts = sorted(set(COUNT_FIELDS) - set(counts))
    if missing_counts:
        raise ValueError(f"record_counts is missing fields: {missing_counts}.")
    for field in COUNT_FIELDS:
        value = counts[field]
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int) or value < 0
        ):
            raise ValueError(f"record_counts.{field} must be a non-negative integer or null.")

    collected, included, excluded = (
        counts["collected"],
        counts["included"],
        counts["excluded"],
    )
    if all(value is not None for value in (collected, included, excluded)):
        if included + excluded != collected:
            raise ValueError(
                "record_counts must satisfy included + excluded = collected."
            )

    development, held_out = counts["development"], counts["held_out"]
    if included is not None and development is not None and held_out is not None:
        if development + held_out > included:
            raise ValueError(
                "development + held_out cannot exceed included records."
            )

    blockers = []
    if manifest["data_status"] != "empirical":
        blockers.append("data_status must be 'empirical' for an empirical release.")
    for field in RELEASE_TEXT_FIELDS:
        if not _non_empty_string(manifest[field]):
            blockers.append(f"{field} must be completed.")
    if not isinstance(annotator_count, int) or isinstance(annotator_count, bool) or annotator_count < 2:
        blockers.append("annotator_count must be at least 2.")
    if not isinstance(double_fraction, (int, float)) or isinstance(double_fraction, bool) or double_fraction <= 0:
        blockers.append("double_annotated_fraction must be greater than 0.")
    if manifest["personal_data_review"] in (None, "", "not-assessed"):
        blockers.append("personal_data_review must document a completed review.")

    if any(counts[field] is None for field in COUNT_FIELDS):
        blockers.append("all record_counts fields must be completed.")
    else:
        if counts["collected"] <= 0 or counts["included"] <= 0:
            blockers.append("collected and included counts must be greater than 0.")
        if counts["development"] <= 0 or counts["held_out"] <= 0:
            blockers.append("development and held_out counts must both be greater than 0.")
        if counts["development"] + counts["held_out"] != counts["included"]:
            blockers.append("development + held_out must equal included for a release.")

    return {
        "manifest_valid": True,
        "release_ready": not blockers,
        "dataset_id": manifest["dataset_id"],
        "version": manifest["version"],
        "data_status": manifest["data_status"],
        "record_counts": counts,
        "release_blockers": blockers,
        "validation_scope": (
            "Metadata structure and arithmetic only. A passing report does not verify "
            "source permissions, truth of declarations, hash provenance, data contents, "
            "annotation correctness, reviewer independence, or representativeness."
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate benchmark provenance metadata and empirical-release fields."
    )
    parser.add_argument("--input", required=True, help="Dataset provenance manifest JSON")
    parser.add_argument(
        "--require-release-ready",
        action="store_true",
        help="Return exit code 1 when empirical-release metadata is incomplete.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        manifest = json.loads(Path(args.input).read_text(encoding="utf-8"))
        report = validate_manifest(manifest)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Manifest validation error: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(report, indent=2, sort_keys=True))
    if args.require_release_ready and not report["release_ready"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
