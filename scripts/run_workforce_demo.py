"""Run the companion workforce CLI and evaluate its exported skill predictions.

The demo uses synthetic job descriptions and reference labels. It is an
integration smoke test, not a representative benchmark or model-quality claim.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

from scripts.evaluate_benchmark import evaluate_records, load_jsonl


def run_workforce_demo(
    jobs_csv: str | Path,
    gold_path: str | Path,
    output_path: str | Path | None = None,
    command: str = "workforce-intel",
) -> dict:
    """Export predictions from workforce-intel and evaluate them by role_id."""
    executable = shutil.which(command)
    if executable is None:
        raise RuntimeError(
            f"Could not find {command!r}. Install the companion project with "
            "'python -m pip install -e path/to/ai-workforce-intelligence'."
        )

    gold_records = load_jsonl(gold_path)
    with __import__("tempfile").TemporaryDirectory(prefix="workforce-demo-") as directory:
        predictions_path = Path(directory) / "predictions.jsonl"
        args = [
            executable,
            str(jobs_csv),
            "--predictions-jsonl",
            str(predictions_path),
            "--json",
        ]
        completed = subprocess.run(args, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or "no error output"
            raise RuntimeError(
                f"{command} exited with status {completed.returncode}: {detail}"
            )
        if not predictions_path.is_file():
            raise RuntimeError(f"{command} completed without writing predictions JSONL.")

        predictions = load_jsonl(predictions_path)
        report = evaluate_records(gold_records, predictions)

    if output_path is not None:
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the synthetic end-to-end workforce extraction evaluation demo."
    )
    parser.add_argument("--jobs-csv", required=True, help="CSV accepted by workforce-intel")
    parser.add_argument("--gold", required=True, help="Reference JSONL with role_id and gold_skills")
    parser.add_argument("--output", help="Optional path for the JSON evaluation report")
    parser.add_argument(
        "--command",
        default="workforce-intel",
        help="Installed workforce CLI command (default: workforce-intel)",
    )
    args = parser.parse_args(argv)

    try:
        report = run_workforce_demo(
            jobs_csv=args.jobs_csv,
            gold_path=args.gold,
            output_path=args.output,
            command=args.command,
        )
    except (OSError, ValueError, RuntimeError) as exc:
        parser.error(str(exc))

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
