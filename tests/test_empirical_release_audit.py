"""Tests for the integrated empirical benchmark release audit."""
import unittest

from scripts.audit_empirical_release import audit_empirical_release
from scripts.validate_annotations import DEFAULT_TAXONOMY_PATH


def complete_manifest():
    return {
        "dataset_id": "synthetic-release-audit-test",
        "version": "0.1.0",
        "data_status": "empirical",
        "source_name": "Synthetic unit-test fixture",
        "source_url": "https://example.org/source",
        "license_name": "Synthetic test terms",
        "license_url": "https://example.org/terms",
        "terms_reviewed_at": "2026-10-31",
        "retrieved_at": "2026-10-31",
        "collection_method": "In-memory synthetic unit-test fixture",
        "content_hash_algorithm": "sha256",
        "source_snapshot_sha256": "a" * 64,
        "taxonomy_version": "aw-intelligence@633da3ef",
        "annotation_protocol_version": "0.1.0",
        "annotator_count": 2,
        "double_annotated_fraction": 0.5,
        "agreement_method": "Pairwise exact-set and Jaccard agreement",
        "adjudication_method": "Independent reviewer adjudication",
        "deduplication_method": "Normalized exact-text deduplication",
        "split_strategy": "Fixed role-ID development and held-out split",
        "record_counts": {
            "collected": 2,
            "included": 2,
            "excluded": 0,
            "development": 1,
            "held_out": 1,
        },
        "personal_data_review": "Synthetic fixtures contain no personal data",
        "notes": "In-memory synthetic unit-test data only; not an empirical dataset.",
    }


def fixture_records():
    final_annotations = [
        {
            "role_id": "role-dev",
            "description": "Python delivery experience.",
            "gold_skills": ["python"],
            "evidence": [{"skill": "python", "quote": "Python"}],
            "annotation_status": "adjudicated",
        },
        {
            "role_id": "role-test",
            "description": "SQL reporting experience.",
            "gold_skills": ["sql"],
            "evidence": [{"skill": "sql", "quote": "SQL"}],
            "annotation_status": "adjudicated",
        },
    ]
    development = [{"role_id": "role-dev", "description": "Python delivery experience."}]
    held_out = [{"role_id": "role-test", "description": "SQL reporting experience."}]
    annotator_a = [
        {
            "role_id": "role-dev",
            "description": "Python delivery experience.",
            "gold_skills": ["python"],
            "evidence": [{"skill": "python", "quote": "Python"}],
            "annotation_status": "draft",
        }
    ]
    annotator_b = [
        {
            "role_id": "role-dev",
            "description": "Python delivery experience.",
            "gold_skills": ["python"],
            "evidence": [{"skill": "python", "quote": "Python"}],
            "annotation_status": "draft",
        }
    ]
    return final_annotations, development, held_out, annotator_a, annotator_b


class TestEmpiricalReleaseAudit(unittest.TestCase):
    def audit(self, manifest=None, records=None):
        final, development, held_out, annotator_a, annotator_b = (
            records or fixture_records()
        )
        return audit_empirical_release(
            manifest or complete_manifest(),
            final,
            development,
            held_out,
            annotator_a,
            annotator_b,
            taxonomy_path=DEFAULT_TAXONOMY_PATH,
        )

    def test_consistent_fixture_passes_all_internal_release_checks(self):
        report = self.audit()
        self.assertTrue(report["release_ready"])
        self.assertTrue(all(report["checks"].values()))
        self.assertEqual(report["observed_double_annotated_fraction"], 0.5)
        self.assertEqual(report["agreement"]["records_compared"], 1)
        self.assertEqual(
            report["annotators"]["annotator_a"]["records_validated"], 1
        )
        self.assertEqual(
            report["annotators"]["annotator_b"]["records_validated"], 1
        )

    def test_incomplete_manifest_is_reported_as_blocked(self):
        manifest = complete_manifest()
        manifest["double_annotated_fraction"] = None
        report = self.audit(manifest=manifest)
        self.assertFalse(report["release_ready"])
        self.assertFalse(report["checks"]["double_annotation_fraction_matches_manifest"])
        self.assertTrue(report["release_blockers"])

    def test_final_annotations_must_be_adjudicated(self):
        records = fixture_records()
        records[0][0]["annotation_status"] = "reviewed"
        with self.assertRaisesRegex(ValueError, "release validation requires 'adjudicated'"):
            self.audit(records=records)

    def test_final_annotation_ids_must_match_split_ids(self):
        records = fixture_records()
        records[1][0]["role_id"] = "different-role"
        report = self.audit(records=records)
        self.assertFalse(report["release_ready"])
        self.assertFalse(report["checks"]["final_annotations_match_split_ids"])

    def test_annotator_coverage_must_match_manifest(self):
        manifest = complete_manifest()
        manifest["double_annotated_fraction"] = 1.0
        report = self.audit(manifest=manifest)
        self.assertFalse(report["release_ready"])
        self.assertFalse(report["checks"]["double_annotation_fraction_matches_manifest"])

    def test_annotator_labels_must_belong_to_taxonomy(self):
        records = fixture_records()
        records[3][0]["gold_skills"] = ["invented skill"]
        records[3][0]["evidence"] = [
            {"skill": "invented skill", "quote": "Python"}
        ]
        with self.assertRaisesRegex(ValueError, "not in taxonomy"):
            self.audit(records=records)

    def test_pre_adjudication_annotator_records_require_evidence(self):
        for annotator_index in (3, 4):
            with self.subTest(annotator_index=annotator_index):
                records = fixture_records()
                records[annotator_index][0].pop("evidence")
                with self.assertRaisesRegex(ValueError, "must contain an evidence list"):
                    self.audit(records=records)

    def test_pre_adjudication_evidence_quote_must_appear_in_description(self):
        records = fixture_records()
        records[3][0]["evidence"] = [
            {"skill": "python", "quote": "GraphQL"}
        ]
        with self.assertRaisesRegex(ValueError, "does not appear in description"):
            self.audit(records=records)


if __name__ == "__main__":
    unittest.main()
