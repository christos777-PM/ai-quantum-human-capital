"""Check development and held-out JSONL files for direct split leakage.

The check catches duplicate role IDs and exact duplicate descriptions after
Unicode compatibility normalization, case-folding, and whitespace collapse.
It does not detect semantic or near-duplicate postings; those still require
a documented human review.
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from typing import Any, Iterable

try:
    from .evaluate_benchmark import load_jsonl
except ImportError:  # Support direct execution as a script.
    from evaluate_benchmark import load_jsonl


def normalize_description(value: str) -> str:
    """Normalize formatting differences before exact cross-split comparison."""
    compatible = unicodedata.normalize("NFKC", value)
    return re.sub(r"\\s+", " ", compatible).strip().casefold()


def _index_split(
    records: Iterable[dict[str, Any]], split_name: str
) -> tuple[dict[str, str], dict[str, str]]:
    """Return normalized role IDs and descriptions mapped to original IDs."""
    role_ids: dict[str, str] = {}
    descriptions: dict[str, str] = {}

    for index, record in enumerate(records, start=1):
        role_id = record.get("role_id")
        if not isinstance(role_id, str) or not role_id.strip():
            raise ValueError(
                f"{split_name} record {index} must have a non-empty role_id."
            )
        original_id = role_id.strip()
        normalized_id = original_id.casefold()
        if normalized_id in role_ids:
            raise ValueError(
                f"{split_name} contains duplicate role_id: {original_id!r}."
            )
        role_ids[normalized_id] = original_id

        description = record.get("description")
        if not isinstance(description, str) or not description.strip():
            raise ValueError(
                f"{split_name} record {original_id!r} must have a non-empty description."
            )
        normalized_description = normalize_description(description)
        if normalized_description in descriptions:
            raise ValueError(
                f"{split_name} contains duplicate normalized descriptions for "
                f"{descriptions[normalized_description]!r} and {original_id!r}."
            )
        descriptions[normalized_description] = original_id

    if not role_ids:
        raise ValueError(f"{split_name} split contains no records.")
    return role_ids, descriptions


def validate_splits(
    development_records: Iterable[dict[str, Any]],
    held_out_records: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Reject record-ID or exact normalized-description overlap between splits."""
    development_ids, development_descriptions = _index_split(
        development_records, "Development"
    )
    held_out_ids, held_out_descriptions = _index_split(
        held_out_records, "Held-out"
    )

    shared_ids = sorted(set(development_ids) & set(held_out_ids))
    if shared_ids:
        originals = [
            f"{development_ids[role_id]!r} (development / "
            f"{held_out_ids[role_id]!r} (held-out)"
            for role_id in shared_ids
        ]
        raise ValueError(
            "role_id overlap between development and held-out splits: "
            + ", ".join(originals)
            + "."
        )

    shared_descriptions = sorted(
        set(development_descriptions) & set(held_out_descriptions)
    )
    if shared_descriptions:
        pairs = [
            f"{development_descriptions[description]!r} (development) and "
            f"{held_out_descriptions[description]!r} (held-out)"
            for description in shared_descriptions
        ]
        raise ValueError(
            "normalized descriptions appear in both splits: "
            + "; ".join(pairs)
            + "."
        )

    return {
        "status": "passed",
        "development_records": len(development_ids),
        "held_out_records": len(held_out_ids),
        "checks": [
            "non-empty unique role IDs within each split",
            "no role ID overlap between splits (case-insensitive)",
            "no duplicate normalized descriptions within either split",
            "no exact normalized description overlap between splits",
        ],
        "description_normalization": (
            "Unicode NFKC, case-folding, and whitespace collapse"
        ),
        "limitations": [
            "semantic and near-duplicate descriptions are not detected",
            "passing does not establish source licensing or annotation quality",
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check development and held-out JSONL files for direct leakage."
    )
    parser.add_argument(
        "--development",
        required=True,
        help="Development JSONL with unique role_id and description fields",
    )
    parser.add_argument(
        "--held-out",
        required=True,
        help="Held-out JSONL with unique role_id and description fields",
    )
    parser.add_argument("--output", help="Optional path for a JSON report")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        report = validate_splits(
            load_jsonl(args.development),
            load_jsonl(args.held_out),
        )
        rendered = json.dumps(report, indent=2, sort_keys=True)
        if args.output:
            from pathlib import Path

            Path(args.output).write_text(rendered + "\\n", encoding="utf-8")
        print(rendered)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
