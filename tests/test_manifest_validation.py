"""Tests for provenance-manifest validation and empirical release gating."""
import copy
import unittest

from scripts.validate_manifest import validate_manifest


def template_manifest():
    return {
        "dataset_id": "replace-with-stable-dataset-id",
        "version": "0.1.0",
        "data_status": "template",
        "source_name": None,
        "source_url": None,
        "license_name": None,
        "license_url": None,
        "terms_reviewed_at": None,
        "retrieved_at": None,
        "collection_method": "replace-with-manual-or-api",
        "content_hash_algorithm": "sha256",
        "source_snapshot_sha256": None,
        "taxonomy_version": "record-a-commit-or-release",
        "annotation_protocol_version": "0.1.0",
        "annotator_count": None,
        "double_annotated_fraction": None,
        "agreement_method": None,
        "adjudication_method": None,
        "deduplication_method": None,
        "split_strategy": None,
        "record_counts": {
            "collected": None,
            "included": None,
            "excluded": None,
            "development": None,
            "held_out": None,
        },
        "personal_data_review": "not-assessed",
        "notes": "Template only.",
    }


def complete_manifest():
    manifest = template_manifest()
    manifest.update(
        {
            "dataset_id": "synthetic-test-dataset",
            "data_status": "empirical",
            "source_name": "Test source",
            "source_url": "https://example.org/dataset",
            "license_name": "CC BY 4.0",
            "license_url": "https://creativecommons.org/licenses/by/4.0/",
            "terms_reviewed_at": "2026-10-30",
            "retrieved_at": "2026-10-30",
            "collection_method": "Documented API export",
            "source_snapshot_sha256": "a" * 64,
            "taxonomy_version": "taxonomy-v1",
            "annotation_protocol_version": "0.1.0",
            "annotator_count": 2,
            "double_annotated_fraction": 1.0,
            "agreement_method": "Pre-adjudication exact-set and per-skill agreement",
            "adjudication_method": "Independent third-reviewer adjudication",
            "deduplication_method": "Normalized exact hash plus manual near-duplicate review",
            "split_strategy": "Grouped by employer before development/held-out split",
            "record_counts": {
                "collected": 12,
                "included": 10,
                "excluded": 2,
                "development": 8,
                "held_out": 2,
            },
            "personal_data_review": "no-personal-data",
            "notes": "Test fixture only; no real source data is represented.",
        }
    )
    return manifest


class TestManifestValidation(unittest.TestCase):
    def test_template_is_structurally_valid_but_not_release_ready(self):
        report = validate_manifest(template_manifest())
        self.assertTrue(report["manifest_valid"])
        self.assertFalse(report["release_ready"])
        self.assertTrue(report["release_blockers"])

    def test_complete_manifest_passes_metadata_release_gate(self):
        report = validate_manifest(complete_manifest())
        self.assertTrue(report["manifest_valid"])
        self.assertTrue(report["release_ready"])
        self.assertEqual(report["release_blockers"], [])

    def test_rejects_missing_schema_field(self):
        manifest = template_manifest()
        del manifest["source_snapshot_sha256"]
        with self.assertRaisesRegex(ValueError, "missing required fields"):
            validate_manifest(manifest)

    def test_rejects_invalid_data_status_type(self):
        manifest = template_manifest()
        manifest["data_status"] = []
        with self.assertRaisesRegex(ValueError, "data_status"):
            validate_manifest(manifest)

    def test_rejects_invalid_source_url(self):
        manifest = complete_manifest()
        manifest["source_url"] = "example.org/dataset"
        with self.assertRaisesRegex(ValueError, "absolute HTTP"):
            validate_manifest(manifest)

    def test_rejects_invalid_review_date(self):
        manifest = complete_manifest()
        manifest["terms_reviewed_at"] = "30-10-2026"
        with self.assertRaisesRegex(ValueError, "YYYY-MM-DD"):
            validate_manifest(manifest)

    def test_rejects_compact_date_format(self):
        manifest = complete_manifest()
        manifest["retrieved_at"] = "20261030"
        with self.assertRaisesRegex(ValueError, "YYYY-MM-DD"):
            validate_manifest(manifest)

    def test_rejects_malformed_snapshot_hash(self):
        manifest = complete_manifest()
        manifest["source_snapshot_sha256"] = "not-a-hash"
        with self.assertRaisesRegex(ValueError, "64 hexadecimal"):
            validate_manifest(manifest)

    def test_rejects_inconsistent_collection_counts(self):
        manifest = complete_manifest()
        manifest["record_counts"]["excluded"] = 3
        with self.assertRaisesRegex(ValueError, "included"):
            validate_manifest(manifest)

    def test_rejects_boolean_record_count(self):
        manifest = complete_manifest()
        manifest["record_counts"]["included"] = True
        with self.assertRaisesRegex(ValueError, "non-negative integer"):
            validate_manifest(manifest)

    def test_rejects_out_of_range_double_annotation_fraction(self):
        manifest = complete_manifest()
        manifest["double_annotated_fraction"] = 1.1
        with self.assertRaisesRegex(ValueError, "between 0 and 1"):
            validate_manifest(manifest)

    def test_one_annotator_blocks_empirical_release(self):
        manifest = complete_manifest()
        manifest["annotator_count"] = 1
        report = validate_manifest(manifest)
        self.assertFalse(report["release_ready"])
        self.assertTrue(
            any("at least 2" in blocker for blocker in report["release_blockers"])
        )

    def test_split_counts_must_cover_all_included_records_for_release(self):
        manifest = complete_manifest()
        manifest["record_counts"]["held_out"] = 1
        report = validate_manifest(manifest)
        self.assertFalse(report["release_ready"])
        self.assertTrue(
            any("must equal included" in blocker for blocker in report["release_blockers"])
        )

    def test_does_not_mutate_input_manifest(self):
        manifest = template_manifest()
        original = copy.deepcopy(manifest)
        validate_manifest(manifest)
        self.assertEqual(manifest, original)


if __name__ == "__main__":
    unittest.main()
