"""Evaluate skill-extraction predictions against an annotated JSONL benchmark.

This module intentionally evaluates predictions rather than generating them, so
rule-based, embedding-based, and LLM-assisted systems can share one metric layer.
Only the Python standard library is required.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """Load JSON objects from a UTF-8 JSON Lines file with line-aware errors."""
    records: list[dict[str, Any]] = []
    source = Path(path)
    with source.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"{source}:{line_number}: invalid JSON: {exc.msg}"
                ) from exc
            if not isinstance(record, dict):
                raise ValueError(f"{source}:{line_number}: each JSONL record must be an object.")
            records.append(record)
    return records


def _index_records(
    records: Iterable[dict[str, Any]],
    skills_field: str,
    label: str,
) -> dict[str, set[str]]:
    indexed: dict[str, set[str]] = {}
    for index, record in enumerate(records, start=1):
        role_id = record.get("role_id")
        if not isinstance(role_id, str) or not role_id.strip():
            raise ValueError(f"{label} record {index} must have a non-empty role_id.")
        role_id = role_id.strip()
        if role_id in indexed:
            raise ValueError(f"{label} contains duplicate role_id: {role_id!r}.")

        skills = record.get(skills_field)
        if not isinstance(skills, list) or any(
            not isinstance(skill, str) or not skill.strip() for skill in skills
        ):
            raise ValueError(
                f"{label} record {role_id!r} must contain a {skills_field!r} list of non-empty strings."
            )
        indexed[role_id] = {skill.strip().casefold() for skill in skills}
    return indexed


def _metrics(true_positive: int, false_positive: int, false_negative: int) -> dict[str, Any]:
    """Return precision, recall and F1; undefined zero-denominator metrics are 0."""
    precision_denominator = true_positive + false_positive
    recall_denominator = true_positive + false_negative
    precision = true_positive / precision_denominator if precision_denominator else 0.0
    recall = true_positive / recall_denominator if recall_denominator else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def evaluate_records(
    benchmark_records: Iterable[dict[str, Any]],
    prediction_records: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Compare gold_skills and predicted_skills by stable role_id.

    Skills are compared as case-insensitive sets after trimming whitespace.
    Micro metrics aggregate counts across all roles; macro_f1 averages the
    rounded per-role F1 values for a simple role-balanced companion measure.
    """
    gold_by_id = _index_records(benchmark_records, "gold_skills", "Benchmark")
    predicted_by_id = _index_records(prediction_records, "predicted_skills", "Predictions")

    if not gold_by_id:
        raise ValueError("Benchmark contains no records.")

    missing = sorted(set(gold_by_id) - set(predicted_by_id))
    extra = sorted(set(predicted_by_id) - set(gold_by_id))
    if missing or extra:
        details = []
        if missing:
            details.append(f"missing predictions for {missing}")
        if extra:
            details.append(f"predictions without benchmark records {extra}")
        raise ValueError("role_id mismatch: " + "; ".join(details) + ".")

    per_role: list[dict[str, Any]] = []
    total_true_positive = 0
    total_false_positive = 0
    total_false_negative = 0

    for role_id in sorted(gold_by_id):
        gold = gold_by_id[role_id]
        predicted = predicted_by_id[role_id]
        true_positive = len(gold & predicted)
        false_positive = len(predicted - gold)
        false_negative = len(gold - predicted)
        metrics = _metrics(true_positive, false_positive, false_negative)
        per_role.append(
            {
                "role_id": role_id,
                "gold_skill_count": len(gold),
                "predicted_skill_count": len(predicted),
                **metrics,
            }
        )
        total_true_positive += true_positive
        total_false_positive += false_positive
        total_false_negative += false_negative

    micro = _metrics(
        total_true_positive,
        total_false_positive,
        total_false_negative,
    )
    macro_f1 = sum(role["f1"] for role in per_role) / len(per_role)

    return {
        "records_evaluated": len(per_role),
        "micro": micro,
        "macro_f1": round(macro_f1, 4),
        "per_role": per_role,
        "metric_notes": {
            "matching": "case-insensitive exact match after trimming; skills are treated as sets",
            "zero_denominator": "precision, recall, or F1 is reported as 0 when its denominator is zero",
            "micro": "precision, recall, and F1 are computed from counts aggregated across all roles",
            "macro_f1": "arithmetic mean of per-role F1 values",
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate predicted skills against a JSONL benchmark."
    )
    parser.add_argument("--gold", required=True, help="Benchmark JSONL with role_id and gold_skills")
    parser.add_argument(
        "--predictions",
        required=True,
        help="Prediction JSONL with role_id and predicted_skills",
    )
    parser.add_argument("--output", help="Optional path for a JSON report")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        report = evaluate_records(load_jsonl(args.gold), load_jsonl(args.predictions))
        rendered = json.dumps(report, indent=2, sort_keys=True)
        if args.output:
            Path(args.output).write_text(rendered + "\n", encoding="utf-8")
        print(rendered)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
