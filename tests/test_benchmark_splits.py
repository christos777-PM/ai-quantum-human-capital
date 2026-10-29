"""Regression tests for development/held-out split leakage checks."""

import unittest

from scripts.validate_benchmark_splits import validate_splits


def record(role_id, description):
    return {"role_id": role_id, "description": description, "source": "synthetic"}


class TestBenchmarkSplitValidation(unittest.TestCase):
    def test_disjoint_synthetic_splits_pass(self):
        report = validate_splits(
            [
                record("dev-001", "Python and cloud delivery."),
                record("dev-002", "VLSI verification planning."),
            ],
            [
                record("test-001", "Quantum algorithms and Qiskit."),
                record("test-002", "Stakeholder and risk management."),
            ],
        )
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["development_records"], 2)
        self.assertEqual(report["held_out_records"], 2)
        self.assertIn(
            "no exact normalized description overlap between splits",
            report["checks"],
        )

    def test_rejects_role_id_overlap_case_insensitively(self):
        with self.assertRaisesRegex(ValueError, "role_id overlap"):
            validate_splits(
                [record("Role-01", "Development description.")],
                [record("role-01", "Different held-out description.")],
            )

    def test_rejects_description_overlap_after_case_and_whitespace_normalization(self):
        with self.assertRaisesRegex(ValueError, "normalized descriptions appear"):
            validate_splits(
                [record("dev-01", "Python   AND\\nCloud")],
                [record("test-01", " python and cloud ")],
            )

    def test_rejects_unicode_compatibility_equivalent_descriptions(self):
        with self.assertRaisesRegex(ValueError, "normalized descriptions appear"):
            validate_splits(
                [record("dev-01", "Build with ＡＰＩ tools.")],
                [record("test-01", "Build with API tools.")],
            )

    def test_rejects_duplicate_descriptions_inside_one_split(self):
        with self.assertRaisesRegex(ValueError, "duplicate normalized descriptions"):
            validate_splits(
                [
                    record("dev-01", "Same description."),
                    record("dev-02", " SAME   DESCRIPTION. "),
                ],
                [record("test-01", "Distinct held-out description.")],
            )

    def test_rejects_duplicate_role_ids_inside_one_split(self):
        with self.assertRaisesRegex(ValueError, "duplicate role_id"):
            validate_splits(
                [
                    record("dev-01", "First description."),
                    record("DEV-01", "Second description."),
                ],
                [record("test-01", "Held-out description.")],
            )

    def test_rejects_empty_splits(self):
        with self.assertRaisesRegex(ValueError, "Development split contains no records"):
            validate_splits(
                [],
                [record("test-01", "Held-out description.")],
            )

    def test_rejects_missing_description(self):
        with self.assertRaisesRegex(ValueError, "non-empty description"):
            validate_splits(
                [{"role_id": "dev-01"}],
                [record("test-01", "Held-out description.")],
            )


if __name__ == "__main__":
    unittest.main()
