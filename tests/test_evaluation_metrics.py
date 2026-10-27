"""Synthetic research tests for benchmark metrics, not candidate or hiring assessments."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.evaluate_benchmark import evaluate_records, load_jsonl


class TestMetrics(unittest.TestCase):
    def test_aggregate_counts_and_metrics(self):
        benchmark = [
            {"role_id": "sample-001", "gold_skills": ["python", "cloud computing", "project management"]},
            {"role_id": "sample-002", "gold_skills": ["python", "qiskit", "linear algebra", "quantum algorithms"]},
        ]
        predictions = [
            {"role_id": "sample-001", "predicted_skills": ["python", "cloud computing", "agile"]},
            {"role_id": "sample-002", "predicted_skills": ["python", "qiskit", "quantum algorithms"]},
        ]

        report = evaluate_records(benchmark, predictions)

        self.assertEqual(report["records_evaluated"], 2)
        self.assertEqual(report["micro"]["true_positive"], 5)
        self.assertEqual(report["micro"]["false_positive"], 1)
        self.assertEqual(report["micro"]["false_negative"], 2)
        self.assertEqual(report["micro"]["precision"], 0.8333)
        self.assertEqual(report["micro"]["recall"], 0.7143)
        self.assertEqual(report["micro"]["f1"], 0.7692)
        self.assertEqual(report["macro_f1"], 0.7619)

    def test_per_role_report_lists_matched_and_error_skills(self):
        report = evaluate_records(
            [{"role_id": "sample", "gold_skills": ["python", "artificial intelligence"]}],
            [{"role_id": "sample", "predicted_skills": ["python", "sql"]}],
        )

        role = report["per_role"][0]
        self.assertEqual(role["matched_skills"], ["python"])
        self.assertEqual(role["false_positive_skills"], ["sql"])
        self.assertEqual(role["false_negative_skills"], ["artificial intelligence"])

    def test_normalizes_skill_labels_as_sets(self):
        report = evaluate_records(
            [{"role_id": "sample", "gold_skills": [" Python "]}],
            [{"role_id": "sample", "predicted_skills": ["python", "PYTHON"]}],
        )
        self.assertEqual(report["micro"]["f1"], 1.0)

    def test_macro_f1_uses_unrounded_per_role_values(self):
        first_predictions = ["hit"] + [f"first-false-positive-{i}" for i in range(98)]
        second_predictions = ["hit"] + [f"second-false-positive-{i}" for i in range(92)]
        report = evaluate_records(
            [
                {"role_id": "sample-001", "gold_skills": ["hit"]},
                {"role_id": "sample-002", "gold_skills": ["hit"]},
            ],
            [
                {"role_id": "sample-001", "predicted_skills": first_predictions},
                {"role_id": "sample-002", "predicted_skills": second_predictions},
            ],
        )
        self.assertEqual(report["per_role"][0]["f1"], 0.02)
        self.assertEqual(report["per_role"][1]["f1"], 0.0213)
        self.assertEqual(report["macro_f1"], 0.0206)

    def test_rejects_duplicate_identifiers(self):
        benchmark = [
            {"role_id": "sample", "gold_skills": ["python"]},
            {"role_id": "sample", "gold_skills": ["sql"]},
        ]
        with self.assertRaisesRegex(ValueError, "duplicate role_id"):
            evaluate_records(benchmark, [])

    def test_rejects_identifier_mismatch(self):
        with self.assertRaisesRegex(ValueError, "role_id mismatch"):
            evaluate_records(
                [{"role_id": "expected", "gold_skills": ["python"]}],
                [{"role_id": "other", "predicted_skills": ["python"]}],
            )

    def test_rejects_empty_benchmark(self):
        with self.assertRaisesRegex(ValueError, "no records"):
            evaluate_records([], [])

    def test_load_jsonl_rejects_non_object_record(self):
        with TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "invalid.jsonl"
            path.write_text('["not", "an object"]\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "each JSONL record must be an object"):
                load_jsonl(path)

    def test_load_jsonl_reports_malformed_line(self):
        with TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "invalid.jsonl"
            path.write_text('{"role_id": "ok"}\n{invalid json}\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid.jsonl:2: invalid JSON"):
                load_jsonl(path)


if __name__ == "__main__":
    unittest.main()
