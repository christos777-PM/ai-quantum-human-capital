"""Check benchmark development/held-out split integrity.

This is a leakage preflight, not proof of statistical independence. It detects
reused role IDs and exact duplicate text after Unicode compatibility, case, and
whitespace normalization, or matching caller-supplied SHA-256 content hashes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from collections import defaultdict
from typing import Any, Iterable

try:
    from .evaluate_benchmark import load_jsonl
except ImportError:  # Support direct execution as a script.
    from evaluate_benchmark import load_jsonl


_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def _role_index(records: Iterable[dict[str, Any]], split_name: str) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(records, start=1):
        role_id = record.get("role_id")
        if not isinstance(role_id, str) or not role_id.strip():
            raise ValueError(f"{split_name} record {index} must have a non-empty role_id.")
        role_id = role_id.strip()
        normalized_id = role_id.casefold()
        if normalized_id in indexed:
            raise ValueError(f"{split_name} contains duplicate role_id: {role_id!r}.")
        indexed[normalized_id] = record
    return indexed


def _content_fingerprint(record: dict[str, Any], *, split_name: str, role_id: str) -> str | None:
    """Prefer a validated SHA-256 fingerprint; otherwise hash normalized text."""
    supplied_hash = record.get("content_sha256")
    if supplied_hash is not None:
        if not isinstance(supplied_hash, str) or not _SHA256_RE.fullmatch(supplied_hash.strip()):
            raise ValueError(
                f"{split_name} record {role_id!r} has an invalid content_sha256; "
                "expected 64 hexadecimal characters."
            )
        return supplied_hash.strip().lower()

    text = record.get("description")
    if text is None:
        text = record.get("text")
    if not isinstance(text, str) or not text.strip():
        return None

    compatible = unicodedata.normalize("NFKC", text)
    normalized = re.sub(r"\s+", " ", compatible).strip().casefold()
    if not normalized:
        return None
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _fingerprint_groups(
    indexed: dict[str, dict[str, Any]], split_name: str
) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for normalized_id, record in indexed.items():
        role_id = record["role_id"].strip()
        fingerprint = _content_fingerprint(record, split_name=split_name, role_id=role_id)
        if fingerprint is not None:
            groups[fingerprint].append(role_id)
    return dict(groups)


def validate_splits(
    development_records: Iterable[dict[str, Any]],
    held_out_records: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Return a deterministic report for role-ID and exact-content leakage."""
    development = _role_index(development_records, "Development")
    held_out = _role_index(held_out_records, "Held-out")

    dev_by_fingerprint = _fingerprint_groups(development, "Development")
    held_by_fingerprint = _fingerprint_groups(held_out, "Held-out")
    dev_duplicates = {
        fingerprint: sorted(ids)
        for fingerprint, ids in dev_by_fingerprint.items()
        if len(ids) > 1
    }
    held_duplicates = {
        fingerprint: sorted(ids)
        for fingerprint, ids in held_by_fingerprint.items()
        if len(ids) > 1
    }

    overlapping_ids = sorted(set(development) & set(held_out))
    cross_duplicates = [
        {
            "development_role_ids": sorted(dev_by_fingerprint[fingerprint]),
            "held_out_role_ids": sorted(held_by_fingerprint[fingerprint]),
        }
        for fingerprint in sorted(set(dev_by_fingerprint) & set(held_by_fingerprint))
    ]

    checks = {
        "development_non_empty": bool(development),
        "held_out_non_empty": bool(held_out),
        "role_ids_disjoint": not overlapping_ids,
        "development_has_no_exact_duplicate_content": not dev_duplicates,
        "held_out_has_no_exact_duplicate_content": not held_duplicates,
        "no_exact_content_shared_across_splits": not cross_duplicates,
    }
    return {
        "passed": all(checks.values()),
        "development_records": len(development),
        "held_out_records": len(held_out),
        "content_fingerprints_checked": sum(map(len, dev_by_fingerprint.values()))
        + sum(map(len, held_by_fingerprint.values())),
        "overlapping_role_ids": overlapping_ids,
        "within_split_duplicate_content": {
            "development": [{"role_ids": ids} for _, ids in sorted(dev_duplicates.items())],
            "held_out": [{"role_ids": ids} for _, ids in sorted(held_duplicates.items())],
        },
        "cross_split_duplicate_content": cross_duplicates,
        "checks": checks,
        "limitations": [
            "Content matching detects exact text after Unicode NFKC, whitespace, and case normalization, not near-duplicates or paraphrases.",
            "Records without description, text, or content_sha256 can only be checked for role-ID overlap.",
            "A passing report does not establish source licensing, annotation quality, representativeness, or statistical independence.",
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check role-ID and exact-content leakage between benchmark splits."
    )
    parser.add_argument("--development", required=True, help="Development JSONL records")
    parser.add_argument("--held-out", required=True, help="Held-out JSONL records")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = validate_splits(
            load_jsonl(args.development),
            load_jsonl(args.held_out),
        )
    except (OSError, ValueError) as exc:
        print(f"Split validation error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
