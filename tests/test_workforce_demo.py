"""Tests for the cross-repository workforce demo runner."""

import json
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from scripts.run_workforce_demo import run_workforce_demo


class TestWorkforceDemo(unittest.TestCase):
    def test_exports_predictions_and_writes_evaluation_report(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            jobs_csv = root / "jobs.csv"
            jobs_csv.write_text("title,description\nExample,Python\n", encoding="utf-8")
            gold_path = root / "gold.jsonl"
            gold_path.write_text(
                json.dumps({"role_id": "example", "gold_skills": ["python"]}) + "\n",
                encoding="utf-8",
            )
            report_path = root / "report.json"

            def fake_run(args, capture_output, text, check):
                prediction_path = Path(args[args.index("--predictions-jsonl") + 1])
                prediction_path.write_text(
                    json.dumps({"role_id": "example", "predicted_skills": ["python"]}) + "\n",
                    encoding="utf-8",
                )
                return subprocess.CompletedProcess(args, 0, stdout="{}", stderr="")

            with patch(
                "scripts.run_workforce_demo.shutil.which",
                return_value="/usr/local/bin/workforce-intel",
            ), patch("scripts.run_workforce_demo.subprocess.run", side_effect=fake_run) as mocked_run:
                report = run_workforce_demo(jobs_csv, gold_path, report_path)

            self.assertEqual(report["records_evaluated"], 1)
            self.assertEqual(report["micro"]["f1"], 1.0)
            self.assertTrue(report_path.is_file())
            self.assertIn("--predictions-jsonl", mocked_run.call_args.args[0])
            self.assertEqual(json.loads(report_path.read_text(encoding="utf-8"))["macro_f1"], 1.0)

    def test_missing_cli_has_actionable_error(self):
        with TemporaryDirectory() as directory:
            gold_path = Path(directory) / "gold.jsonl"
            gold_path.write_text(
                json.dumps({"role_id": "example", "gold_skills": ["python"]}) + "\n",
                encoding="utf-8",
            )
            with patch("scripts.run_workforce_demo.shutil.which", return_value=None):
                with self.assertRaisesRegex(RuntimeError, "Install the companion project"):
                    run_workforce_demo("jobs.csv", gold_path)

    def test_cli_failure_surfaces_stderr(self):
        with TemporaryDirectory() as directory:
            gold_path = Path(directory) / "gold.jsonl"
            gold_path.write_text(
                json.dumps({"role_id": "example", "gold_skills": ["python"]}) + "\n",
                encoding="utf-8",
            )
            with patch(
                "scripts.run_workforce_demo.shutil.which",
                return_value="/usr/local/bin/workforce-intel",
            ), patch(
                "scripts.run_workforce_demo.subprocess.run",
                return_value=subprocess.CompletedProcess(["workforce-intel"], 2, stdout="", stderr="bad CSV"),
            ):
                with self.assertRaisesRegex(RuntimeError, "bad CSV"):
                    run_workforce_demo("jobs.csv", gold_path)


if __name__ == "__main__":
    unittest.main()
