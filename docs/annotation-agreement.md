# Pairwise annotation agreement

The repository includes `scripts/compare_annotations.py` to compare two independent annotators' canonical skill-label sets before adjudication.

## Run it

Each JSONL input needs one object per record with a stable `role_id` and a `gold_skills` list. The two files must contain the same role IDs.

```bash
python scripts/compare_annotations.py \
  --annotator-a path/to/annotator-a.jsonl \
  --annotator-b path/to/annotator-b.jsonl \
  --output /tmp/annotation-agreement.json
```

## Reported measures

- **Exact-set agreement:** proportion of records for which both annotators assigned exactly the same skill set.
- **Mean role-level Jaccard:** average, across records, of the intersection divided by the union of the two skill sets. A pair of empty skill sets is defined as Jaccard 1.0 and should be interpreted carefully.
- **Micro Jaccard:** total shared role-skill labels divided by the total distinct role-skill labels across both annotators.
- **Per-role disagreement lists:** labels only annotator A or only annotator B assigned, to support review and adjudication.
- **Per-skill one-vs-rest Cohen's kappa:** for each observed skill, treats presence/absence across roles as a binary label and reports both-present, annotator-only, and both-absent counts, observed agreement, expected agreement, and kappa.
- **Mean per-skill kappa:** unweighted mean of defined per-skill kappas. The report also gives the number of labels included in this mean.

Role IDs and labels are trimmed and case-folded. Label comparison is exact after that normalization; the tool does not infer synonyms. Duplicate IDs, duplicate labels after normalization, malformed labels, empty files, and mismatched role-ID sets are rejected.

## Interpreting Cohen's kappa

For each skill, Cohen's kappa is calculated as:

`(observed agreement - expected agreement) / (1 - expected agreement)`

Expected agreement is calculated from the two annotators' positive and negative label prevalence across the matched roles. Kappa is reported as `null` when expected agreement is 1.0, because the denominator is zero and the statistic is undefined. The mean excludes undefined labels and is unweighted.

Per-skill kappa can be unstable when the number of roles is small or a skill is very rare. Prevalence effects can also make kappa look different from raw agreement. Read it alongside the confusion counts, exact-set agreement, Jaccard measures and the underlying per-role disagreements. Do not apply universal pass/fail thresholds to a tiny sample.

## Interpretation and limitations

These are consistency measures, not proof of correctness. They do not establish that annotators worked independently, that either annotator is correct, or that adjudication was unbiased. Agreement should be computed on independent annotations **before** adjudication. Record annotator instructions, training, double-annotation coverage, disagreements and adjudication decisions in the dataset manifest or accompanying study notes.

The committed `annotator-a.example.jsonl` and `annotator-b.example.jsonl` files are synthetic CI fixtures only. Their scores are not empirical results and must not be cited as human inter-annotator agreement.
