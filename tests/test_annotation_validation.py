"""Tests for taxonomy membership and annotation evidence validation."""

import unittest
from pathlib import Path

from scripts.validate_annotations import load_taxonomy, validate_annotation_records


ROOT = Path(__file__).resolve().parents[1]


def record(**overrides):
    item = {
        "role_id": "synthetic-001",
        "description": "Synthetic example: Python and REST APIs support delivery.",
        "gold_skills": ["python", "rest api"],
        "evidence": [
            {"skill": "python", "quote": "Python"},
            {"skill": "rest api", "quote": "REST APIs"},
        ],
        "annotation_status": "draft",
    }
    item.update(overrides)
    return item


class TestAnnotationValidation(unittest.TestCase):
    def test_valid_record_returns_summary_with_taxonomy_version(self):
        report = validate_annotation_records([record()])
        self.assertEqual(report["records_validated"], 1)
        self.assertEqual(report["skill_labels_validated"], 2)
        self.assertEqual(report["annotation_status_counts"], {"draft": 1})
        self.assertEqual(report["taxonomy_version"], "aw-intelligence@2d1192cc")

    def test_bundled_taxonomy_contains_expected_canonical_labels(self):
        skills, version = load_taxonomy(
            ROOT / "data" / "benchmark" / "taxonomy-v1.json"
        )
        self.assertIn("artificial intelligence", skills)
        self.assertIn("rest api", skills)
        self.assertEqual(version, "aw-intelligence@2d1192cc")

    def test_rejects_label_not_in_canonical_taxonomy(self):
        item = record(
            description="Synthetic example: quantum supremacy research.",
            gold_skills=["quantum supremacy"],
            evidence=[{"skill": "quantum supremacy", "quote": "quantum supremacy"}],
        )
        with self.assertRaisesRegex(ValueError, "not in taxonomy"):
            validate_annotation_records([item])

    def test_custom_taxonomy_is_case_insensitive(self):
        report = validate_annotation_records(
            [record(gold_skills=["PYTHON", "REST API"])],
            allowed_skills={"Python", "REST API"},
            taxonomy_version="test-taxonomy-v1",
        )
        self.assertEqual(report["taxonomy_version"], "test-taxonomy-v1")

    def test_quote_matching_ignores_case_and_whitespace(self):
        item = record(
            description="Python\nhelps teams use REST APIs.",
            evidence=[
                {"skill": "python", "quote": "PYTHON"},
                {"skill": "rest api", "quote": "REST   APIs"},
            ],
        )
        self.assertEqual(validate_annotation_records([item])["records_validated"], 1)

    def test_empty_label_set_is_allowed_without_evidence(self):
        item = record(gold_skills=[], evidence=[])
        self.assertEqual(validate_annotation_records([item])["skill_labels_validated"], 0)

    def test_rejects_duplicate_role_ids(self):
        with self.assertRaisesRegex(ValueError, "duplicate role_id"):
            validate_annotation_records([record(), record()])

    def test_rejects_duplicate_labels(self):
        item = record(
            gold_skills=["python", " Python "],
            evidence=[{"skill": "python", "quote": "Python"}],
        )
        with self.assertRaisesRegex(ValueError, "duplicate gold_skills"):
            validate_annotation_records([item])

    def test_rejects_quote_not_in_description(self):
        item = record(evidence=[
            {"skill": "python", "quote": "Python"},
            {"skill": "rest api", "quote": "GraphQL"},
        ])
        with self.assertRaisesRegex(ValueError, "does not appear in description"):
            validate_annotation_records([item])

    def test_rejects_gold_label_without_evidence(self):
        item = record(evidence=[{"skill": "python", "quote": "Python"}])
        with self.assertRaisesRegex(ValueError, "missing evidence"):
            validate_annotation_records([item])

    def test_rejects_evidence_for_unlabelled_skill(self):
        item = record(evidence=[
            {"skill": "python", "quote": "Python"},
            {"skill": "rest api", "quote": "REST APIs"},
            {"skill": "sql", "quote": "delivery"},
        ])
        with self.assertRaisesRegex(ValueError, "unlabelled skill"):
            validate_annotation_records([item])

    def test_release_mode_requires_adjudicated_status(self):
        with self.assertRaisesRegex(ValueError, "requires 'adjudicated'"):
            validate_annotation_records([record()], require_adjudicated=True)
        reviewed = record(annotation_status="adjudicated")
        self.assertEqual(
            validate_annotation_records([reviewed], require_adjudicated=True)["records_validated"],
            1,
        )

    def test_rejects_unknown_status(self):
        with self.assertRaisesRegex(ValueError, "annotation_status"):
            validate_annotation_records([record(annotation_status="approved")])

    def test_rejects_empty_input(self):
        with self.assertRaisesRegex(ValueError, "contains no records"):
            validate_annotation_records([])


if __name__ == "__main__":
    unittest.main()
