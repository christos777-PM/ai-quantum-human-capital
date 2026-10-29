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

Role IDs and labels are trimmed and case-folded. Label comparison is exact after that normalization; the tool does not infer synonyms. Duplicate IDs, duplicate labels after normalization, malformed labels, empty files, and mismatched role-ID sets are rejected.

## Interpretation and limitations

These are transparent, descriptive measures for multi-label annotation consistency, not a chance-corrected statistic. They do not establish that either annotator is correct, that annotators worked independently, or that adjudication was unbiased. Agreement should be computed on the independent annotations **before** adjudication. Record annotator instructions, training, double-annotation coverage, disagreements and adjudication decisions in the dataset manifest or accompanying study notes.

The committed `annotator-a.example.jsonl` and `annotator-b.example.jsonl` files are synthetic CI fixtures only. Their scores are not empirical results and must not be cited as human inter-annotator agreement.
