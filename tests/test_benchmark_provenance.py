"""Guardrails for benchmark provenance and synthetic fixture labeling."""

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_DIR = ROOT / "data" / "benchmark"


class TestBenchmarkProvenance(unittest.TestCase):
    def test_manifest_template_is_valid_and_has_required_fields(self):
        manifest = json.loads(
            (BENCHMARK_DIR / "manifest.template.json").read_text(encoding="utf-8")
        )
        required = {
            "dataset_id",
            "version",
            "data_status",
            "source_name",
            "source_url",
            "license_name",
            "terms_reviewed_at",
            "retrieved_at",
            "content_hash_algorithm",
            "taxonomy_version",
            "annotation_protocol_version",
            "annotator_count",
            "agreement_method",
            "adjudication_method",
            "deduplication_method",
            "split_strategy",
            "record_counts",
            "personal_data_review",
        }
        self.assertTrue(required.issubset(manifest))
        self.assertEqual(manifest["data_status"], "template")
        self.assertEqual(manifest["content_hash_algorithm"], "sha256")
        self.assertIsNone(manifest["source_url"])
        self.assertEqual(manifest["personal_data_review"], "not-assessed")

    def test_bundled_reference_fixtures_are_explicitly_synthetic(self):
        for filename in ("example.jsonl", "workforce_demo_gold.jsonl"):
            with self.subTest(filename=filename):
                path = BENCHMARK_DIR / filename
                records = [
                    json.loads(line)
                    for line in path.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
                self.assertTrue(records, f"{filename} should not be empty")
                self.assertTrue(
                    all(record.get("source") == "synthetic" for record in records),
                    f"{filename} must label every record as synthetic",
                )


if __name__ == "__main__":
    unittest.main()
