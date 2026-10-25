# Workforce skill benchmark

This directory contains a small **synthetic example** for exercising the benchmark evaluator. It is not a real job-posting dataset and must not be used to claim labor-market trends or model performance.

## Files

- `example.jsonl`: reference records with `role_id` and `gold_skills`. The optional `source` and `description` fields preserve context but are not used by the metric calculation.
- `example_predictions.jsonl`: example predictions keyed by the same `role_id`, with `predicted_skills`.

Each non-empty line is a JSON object. The `role_id` must be non-empty and unique within each file. Skill arrays must contain non-empty strings. Skills are trimmed, case-folded and compared as sets, so duplicates and capitalization differences do not affect the score.

## Run the example

From the repository root:

```bash
python scripts/evaluate_benchmark.py \
  --gold data/benchmark/example.jsonl \
  --predictions data/benchmark/example_predictions.jsonl \
  --output /tmp/benchmark-report.json
```

The report includes:

- **Per-role metrics:** true positives, false positives, false negatives, precision, recall and F1.
- **Micro metrics:** counts aggregated across all roles before calculating precision, recall and F1.
- **Macro F1:** arithmetic mean of the unrounded per-role F1 values, rounded to four decimal places.

A metric with a zero denominator is reported as `0`. Matching is exact after trimming and case-folding; no synonym or semantic matching is attempted. Missing or extra role IDs, duplicate IDs, malformed JSONL and invalid skill arrays are rejected.

## Research-quality requirements before empirical use

1. Use public, appropriately licensed or synthetic source material. Preserve provenance and license notes.
2. Define and version the canonical skill taxonomy before annotating the evaluation set.
3. Have human reviewers apply a written annotation guide; record disagreements and adjudication.
4. Keep the benchmark version and prediction method/configuration fixed when comparing runs.
5. Separate development examples from held-out evaluation records to reduce leakage.
6. Do not include personal candidate information or make individual hiring/suitability decisions from these metrics.

The bundled data is only a deterministic smoke test. It does not validate the taxonomy, the extractor, or any real-world workforce claim.
