"""Tests for benchmark split leakage checks."""
import hashlib
import unittest

from scripts.validate_splits import validate_splits


class TestValidateSplits(unittest.TestCase):
    def test_disjoint_records_pass(self):
        report = validate_splits(
            [{"role_id": "dev-1", "description": "Python and cloud computing"}],
            [{"role_id": "test-1", "description": "Quantum algorithms and Qiskit"}],
        )
        self.assertTrue(report["passed"])
        self.assertEqual(report["content_fingerprints_checked"], 2)

    def test_overlapping_role_id_fails(self):
        report = validate_splits(
            [{"role_id": "same", "gold_skills": ["python"]}],
            [{"role_id": "same", "gold_skills": ["python"]}],
        )
        self.assertFalse(report["passed"])
        self.assertEqual(report["overlapping_role_ids"], ["same"])

    def test_normalized_duplicate_text_across_splits_fails(self):
        report = validate_splits(
            [{"role_id": "dev-1", "description": "Python   and\ncloud computing"}],
            [{"role_id": "test-1", "description": " python and cloud COMPUTING "}],
        )
        self.assertFalse(report["passed"])
        self.assertEqual(
            report["cross_split_duplicate_content"],
            [{"development_role_ids": ["dev-1"], "held_out_role_ids": ["test-1"]}],
        )

    def test_duplicate_text_within_one_split_fails(self):
        report = validate_splits(
            [
                {"role_id": "dev-1", "description": "Python"},
                {"role_id": "dev-2", "description": " python "},
            ],
            [{"role_id": "test-1", "description": "Qiskit"}],
        )
        self.assertFalse(report["passed"])
        self.assertEqual(
            report["within_split_duplicate_content"]["development"],
            [{"role_ids": ["dev-1", "dev-2"]}],
        )

    def test_content_sha256_detects_leakage_without_raw_text(self):
        fingerprint = hashlib.sha256(b"permitted-source-record").hexdigest()
        report = validate_splits(
            [{"role_id": "dev-1", "content_sha256": fingerprint}],
            [{"role_id": "test-1", "content_sha256": fingerprint.upper()}],
        )
        self.assertFalse(report["passed"])
        self.assertEqual(len(report["cross_split_duplicate_content"]), 1)

    def test_invalid_hash_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid content_sha256"):
            validate_splits(
                [{"role_id": "dev-1", "content_sha256": "not-a-sha"}],
                [{"role_id": "test-1", "description": "Qiskit"}],
            )

    def test_empty_split_fails(self):
        report = validate_splits(
            [{"role_id": "dev-1", "description": "Python"}],
            [],
        )
        self.assertFalse(report["passed"])
        self.assertFalse(report["checks"]["held_out_non_empty"])


if __name__ == "__main__":
    unittest.main()
