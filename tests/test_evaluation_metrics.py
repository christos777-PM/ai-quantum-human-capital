"""Synthetic research tests for benchmark metrics, not candidate or hiring assessments."""

import unittest

from scripts.evaluate_benchmark import evaluate_records


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

    def test_normalizes_skill_labels_as_sets(self):
        report = evaluate_records(
            [{"role_id": "sample", "gold_skills": [" Python "]}],
            [{"role_id": "sample", "predicted_skills": ["python", "PYTHON"]}],
        )
        self.assertEqual(report["micro"]["f1"], 1.0)

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


if __name__ == "__main__":
    unittest.main()
