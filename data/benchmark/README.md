# Workforce skill benchmark

This directory contains small **synthetic examples** for exercising the benchmark evaluator. They are not real job-posting data and must not be used to claim labor-market trends or model performance.

## Files

- \`example.jsonl\`: reference records with \`role_id\` and \`gold_skills\`. The optional \`source\` and \`description\` fields preserve context but are not used by the metric calculation.
- \`example_predictions.jsonl\`: example predictions keyed by the same \`role_id\`, with \`predicted_skills\`.
- \`workforce_demo_gold.jsonl\`: synthetic reference labels for the five-role companion integration smoke test.
- \`annotation-example.jsonl\`: one synthetic evidence-linked annotation record, intentionally marked \`draft\`.
- \`annotator-a.example.jsonl\` and \`annotator-b.example.jsonl\`: synthetic fixtures for testing pairwise agreement metrics; they are not human annotator results.
- \`annotation_protocol.md\`: labeling, evidence, adjudication, provenance and held-out evaluation rules for future empirical work.
- \`manifest.template.json\`: machine-readable template for recording dataset source, license review, taxonomy version, annotation and split details.
- \`taxonomy-v1.json\`: frozen snapshot of canonical labels from the companion extractor taxonomy at source commit \`633da3ef\`. Update this snapshot deliberately when the source taxonomy changes.
- \`splits/development.example.jsonl\` and \`splits/held_out.example.jsonl\`: synthetic fixtures for testing the split-integrity preflight.

Each non-empty line in evaluator JSONL is a JSON object. The \`role_id\` must be non-empty and unique within each file. Skill arrays must contain non-empty strings. Skills are trimmed, case-folded and compared as sets, so duplicates and capitalization differences do not affect the score.

## Validate dataset provenance before empirical release

Use the manifest validator to check the provenance JSON structure, date and URL formats, SHA-256 fingerprint shape, and record-count arithmetic:

\`\`\`bash
python scripts/validate_manifest.py --input data/benchmark/manifest.template.json
\`\`\`

The template is expected to pass structural validation while reporting that it is **not release-ready**. Once a dataset manifest is completed, add \`--require-release-ready\` to make missing empirical-release metadata return a non-zero exit code:

\`\`\`bash
python scripts/validate_manifest.py \\
  --input path/to/dataset-manifest.json \\
  --require-release-ready
\`\`\`

The release gate requires a documented source and license/terms review, retrieval date, source snapshot SHA-256, taxonomy and annotation-protocol versions, at least two annotators, non-zero double-annotation coverage, agreement and adjudication methods, deduplication and split strategies, a completed personal-data review, and internally consistent collected/included/excluded and development/held-out counts. Development and held-out counts must sum to the included count.

A passing result means only that the declared metadata is complete and internally consistent. The validator cannot verify that a license permits the intended use, that a hash matches the source, that annotations are correct, that reviewers worked independently, or that the sample is representative. Those claims still require evidence and human review. Do not mark a dataset empirical merely to make the gate pass.

## Validate annotation evidence and taxonomy membership

Before evaluating human annotations, validate that each canonical label is in the frozen taxonomy snapshot and linked to a quote present in its source description:

\`\`\`bash
python scripts/validate_annotations.py --input data/benchmark/annotation-example.jsonl
\`\`\`

The bundled taxonomy snapshot is used by default. To validate against another reviewed taxonomy version, pass \`--taxonomy path/to/taxonomy.json\`. The file must contain a non-empty \`taxonomy_version\` and a unique \`canonical_skills\` list.

The validator rejects duplicate record IDs and labels, labels absent from the canonical taxonomy, missing evidence, quotes absent from the description, and evidence for labels not included in \`gold_skills\`. Empty label sets are permitted. For a release candidate, use \`--require-adjudicated\` to require each record's status to be \`adjudicated\`.

This is a structural and taxonomy-membership check, not proof of semantic label correctness, source licensing, independent review, or honest adjudication. The taxonomy is a frozen copy of the companion repository, so reviewers should compare its recorded source commit with the intended extractor version. The bundled annotation record is synthetic and marked \`draft\`; it does not represent completed annotation work.

## Compare two annotators before adjudication

Use the pairwise agreement report on two independent annotation files before adjudication:

\`\`\`bash
python scripts/compare_annotations.py \\
  --annotator-a path/to/annotator-a.jsonl \\
  --annotator-b path/to/annotator-b.jsonl \\
  --output /tmp/annotation-agreement.json
\`\`\`

The report includes exact-set agreement, mean role-level Jaccard, micro Jaccard, per-role disagreement lists, and one-vs-rest Cohen's kappa for each observed skill across roles. Each per-skill result includes both-present, annotator-only and both-absent counts, observed agreement, expected agreement and kappa. The mean per-skill kappa is unweighted and excludes labels for which kappa is undefined because expected agreement is 1.0.

Kappa can be unstable for rare skills and small samples, and prevalence affects its interpretation. Read it alongside the raw counts and descriptive set metrics; do not apply universal thresholds to a tiny sample. Both files must contain the same unique role IDs and each record must contain a \`gold_skills\` list. Label matching is exact after trimming and case-folding; synonyms are not inferred.

These measures quantify consistency, not correctness. They do not prove annotator independence or unbiased adjudication. Agreement should be computed before adjudication. See [the annotation agreement guide](../../docs/annotation-agreement.md) for interpretation and limitations. The committed A/B files are synthetic CI fixtures only, not empirical inter-annotator agreement results.

## Check development/held-out split leakage

Before reporting held-out metrics, check that the development and held-out files do not reuse role IDs or exact duplicate content:

\`\`\`bash
python scripts/validate_splits.py \\
  --development data/benchmark/splits/development.example.jsonl \\
  --held-out data/benchmark/splits/held_out.example.jsonl
\`\`\`

The validator rejects empty splits, duplicate role IDs within or across files, repeated content within either split, and exact content matches across splits. It fingerprints \`description\` or \`text\` after Unicode NFKC, whitespace and case normalization; when raw text cannot be retained, a caller-supplied 64-character \`content_sha256\` can be used instead. The report lists offending IDs without printing source text.

This is a leakage preflight, not a guarantee of independence. It does not detect paraphrases or near-duplicates, and records without text or a content hash can only be checked for role-ID overlap. A passing result does not establish licensing, annotation quality, representativeness or statistical independence. CI exercises the command with synthetic fixtures only.

## Run the metric example

From the repository root:

\`\`\`bash
python scripts/evaluate_benchmark.py \\
  --gold data/benchmark/example.jsonl \\
  --predictions data/benchmark/example_predictions.jsonl \\
  --output /tmp/benchmark-report.json
\`\`\`

The report includes per-role precision, recall and F1, matched labels, false positives, false negatives, micro metrics and macro F1. Skill matching is exact after trimming and case-folding; no synonym or semantic matching is attempted. Missing or extra role IDs, duplicate IDs, malformed JSONL and invalid skill arrays are rejected.

## End-to-end companion integration

Install the companion project in a sibling directory, then run the extractor and evaluator as one reproducible flow:

\`\`\`bash
python -m pip install -e ../ai-workforce-intelligence
python scripts/run_workforce_demo.py \\
  --jobs-csv ../ai-workforce-intelligence/data/sample_jobs.csv \\
  --gold data/benchmark/workforce_demo_gold.jsonl \\
  --output /tmp/workforce-demo-report.json
\`\`\`

The runner invokes \`workforce-intel --predictions-jsonl\`, validates role-ID alignment through the evaluator, and writes per-role and aggregate metrics. CI checks this path against the companion repository's current \`main\` branch. The five-role reference file is synthetic and exercises the current explicit plural and AI abbreviation aliases.

With the companion extractor's explicit aliases, the five-role fixture is expected to report micro precision, recall, F1 and macro F1 of \`1.0000\`, with no false-positive or false-negative labels. These exact values are regression targets for this fixed synthetic fixture only, not evidence of generalization or labor-market accuracy.

## Research-quality requirements before empirical use

Follow the [human-reviewed annotation protocol](annotation_protocol.md) and complete a copy of [the provenance manifest template](manifest.template.json) before treating any dataset as empirical.

At minimum:

1. Use public, appropriately licensed or synthetic source material and verify terms before republishing text.
2. Define and version the canonical skill taxonomy before annotating the evaluation set.
3. Have human reviewers apply a written annotation guide; record disagreements and adjudication.
4. Record pre-adjudication agreement from independent annotations, including the agreement method and double-annotation coverage.
5. Keep the benchmark version and prediction method/configuration fixed when comparing runs.
6. Separate development examples from held-out evaluation records to reduce leakage.
7. Do not include personal candidate information or make individual hiring/suitability decisions from these metrics.

The bundled data is only a deterministic smoke test. It does not validate the taxonomy, the extractor, or any real-world workforce claim.
