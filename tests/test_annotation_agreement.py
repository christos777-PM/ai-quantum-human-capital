"""Tests for pairwise multi-label annotation agreement."""
import unittest

from scripts.compare_annotations import compare_annotations


class TestCompareAnnotations(unittest.TestCase):
    def test_identical_annotations_have_full_agreement(self):
        a = [
            {"role_id": "role-1", "gold_skills": ["python", "rest api"]},
            {"role_id": "role-2", "gold_skills": []},
        ]
        report = compare_annotations(a, a)
        self.assertEqual(report["records_compared"], 2)
        self.assertEqual(report["exact_set_agreement"], 1.0)
        self.assertEqual(report["mean_role_jaccard"], 1.0)
        self.assertEqual(report["micro_jaccard"], 1.0)

    def test_reports_exact_set_mean_and_micro_jaccard(self):
        a = [
            {"role_id": "role-1", "gold_skills": ["python", "rest api"]},
            {"role_id": "role-2", "gold_skills": ["sql"]},
            {"role_id": "role-3", "gold_skills": []},
        ]
        b = [
            {"role_id": "role-1", "gold_skills": ["Python", "REST API"]},
            {"role_id": "role-2", "gold_skills": ["sql", "cloud computing"]},
            {"role_id": "role-3", "gold_skills": []},
        ]
        report = compare_annotations(a, b)
        self.assertEqual(report["exact_set_matches"], 2)
        self.assertEqual(report["exact_set_agreement"], 0.6667)
        self.assertEqual(report["mean_role_jaccard"], 0.8333)
        self.assertEqual(report["micro_jaccard"], 0.75)
        self.assertEqual(
            report["per_role"][1]["only_annotator_b"], ["cloud computing"]
        )

    def test_role_id_matching_ignores_case_and_whitespace(self):
        report = compare_annotations(
            [{"role_id": " Role-1 ", "gold_skills": ["Python"]}],
            [{"role_id": "role-1", "gold_skills": [" python "]}],
        )
        self.assertEqual(report["exact_set_agreement"], 1.0)

    def test_rejects_mismatched_role_ids(self):
        with self.assertRaisesRegex(ValueError, "role_id mismatch"):
            compare_annotations(
                [{"role_id": "role-a", "gold_skills": ["python"]}],
                [{"role_id": "role-b", "gold_skills": ["python"]}],
            )

    def test_rejects_duplicate_role_ids_after_normalization(self):
        with self.assertRaisesRegex(ValueError, "duplicate role_id"):
            compare_annotations(
                [
                    {"role_id": "role-1", "gold_skills": ["python"]},
                    {"role_id": "ROLE-1", "gold_skills": ["sql"]},
                ],
                [{"role_id": "role-1", "gold_skills": ["python"]}],
            )

    def test_rejects_duplicate_skill_labels_after_normalization(self):
        with self.assertRaisesRegex(ValueError, "duplicate gold_skills"):
            compare_annotations(
                [{"role_id": "role-1", "gold_skills": ["Python", " python "]}],
                [{"role_id": "role-1", "gold_skills": ["python"]}],
            )

    def test_rejects_malformed_skill_labels(self):
        with self.assertRaisesRegex(ValueError, "non-empty strings"):
            compare_annotations(
                [{"role_id": "role-1", "gold_skills": ["python", " "]}],
                [{"role_id": "role-1", "gold_skills": ["python"]}],
            )

    def test_rejects_empty_annotator_input(self):
        with self.assertRaisesRegex(ValueError, "contains no annotation records"):
            compare_annotations(
                [],
                [{"role_id": "role-1", "gold_skills": ["python"]}],
            )


if __name__ == "__main__":
    unittest.main()
