# Human-reviewed skill benchmark annotation protocol

**Status:** protocol template for future empirical evaluation. The benchmark files currently committed in this repository are synthetic fixtures, not human-annotated job-market data.

## 1. Purpose and unit of annotation

The unit is one job-description record, identified by a stable, unique `role_id`. Annotate the exact description text supplied to the extractor. The title may be retained as context, but do not use skills that appear only in the title as gold labels when the extractor does not receive the title as input.

The objective is to record which skills from a fixed, versioned taxonomy are explicitly mentioned in the text. This is a skill-extraction benchmark, not an assessment of role quality, skill importance, candidate competence, or hiring suitability.

## 2. Labeling rules

1. **Use canonical taxonomy labels.** Every gold label must exist in the taxonomy version recorded for the dataset.
2. **Require textual evidence.** Include a skill when the description explicitly names it as a tool, method, technology, capability, qualification, or work responsibility. Do not infer skills from an employer name, product name, job seniority, or what a role would normally require.
3. **Apply only approved aliases.** Map a surface form to a canonical label only when that mapping exists in the versioned alias table. For example, `AI` maps to `artificial intelligence`, `APIs` maps to `api`, and `LLMs` maps to `llm`. Do not silently invent synonyms during annotation.
4. **Resolve overlapping phrases consistently.** Follow the extractor's longest-phrase policy. For `REST APIs`, label `rest api` rather than also labeling the overlapping `api`. If the text separately mentions `REST APIs and APIs`, both canonical labels may be present.
5. **Do not double-count repeated mentions.** The evaluator treats skill labels as sets. Include each canonical label at most once per record.
6. **Allow an empty label set.** If the description contains no taxonomy skills, use an empty `gold_skills` list rather than guessing.
7. **Flag ambiguity.** If the evidence is unclear or the taxonomy lacks a suitable label, record the case in an adjudication log. Change the taxonomy through a separately versioned decision, not silently in the gold labels.

## 3. Annotation workflow

1. Freeze and record the taxonomy version and this protocol version before annotating the held-out set.
2. Train annotators on a small pilot set that is excluded from final held-out scoring.
3. Have two annotators independently label the held-out records where feasible. For a very small benchmark, aim to double-annotate every held-out record.
4. Compare labels by role and by canonical skill. Record disagreements, the evidence text, the final decision, and the reason for adjudication.
5. Have a designated adjudicator resolve disagreements without using the extractor's prediction as the deciding authority.
6. Re-run quality checks after adjudication and freeze the gold file before evaluating a candidate extractor.

Report the number of annotators, the proportion double-annotated, the agreement method and result, and how disagreements were resolved. Do not report agreement only after adjudication as though it were independent agreement.

## 4. Record format and identifiers

Reference JSONL records use `role_id` and `gold_skills`. Keep IDs stable between the source CSV, predictions, and reference labels. Prefer an opaque source identifier or a documented deterministic ID; avoid title-only IDs if duplicate titles are possible. Reject duplicate IDs instead of assigning order-dependent suffixes.

Optional metadata may include a source class, collection date, taxonomy version, annotation status, or a pointer to a separate adjudication log. Do not put personal candidate data in the benchmark. Do not include full source text or source URLs in a public repository unless the source terms permit it.

### Evidence-linked annotation records

For annotation work, use the stricter record format accepted by `scripts/validate_annotations.py`:

```json
{
  "role_id": "stable-record-id",
  "description": "The exact description text supplied to the extractor.",
  "gold_skills": ["python"],
  "evidence": [
    {"skill": "python", "quote": "Python"}
  ],
  "annotation_status": "draft"
}
```

Each gold label must have at least one evidence quote copied from the description. Quotes are checked after case-folding and whitespace normalization. Evidence entries cannot refer to labels absent from `gold_skills`; duplicate labels and duplicate role IDs are rejected. An empty `gold_skills` list is valid when the description contains no taxonomy skills.

Run the validator before using annotations:

```bash
python scripts/validate_annotations.py --input data/benchmark/annotation-example.jsonl
```

For a release candidate, add `--require-adjudicated`; every record must then carry `"annotation_status": "adjudicated"`. This is a workflow gate only. It does **not** verify semantic correctness, taxonomy membership, source licensing, independent review, or whether adjudication was performed honestly. Those still require human review and the completed provenance manifest. The committed annotation example is synthetic and marked `draft`, not empirical or human-reviewed data.

## 5. Provenance and licensing

For every empirical dataset version, complete a copy of `manifest.template.json` and retain the evidence needed to substantiate each field.

Record at minimum:

- Source name and source URL or stable source identifier, where permitted
- Retrieval date and collection method
- Applicable license and terms-of-use review date
- A SHA-256 content hash for the source snapshot or permitted stored artifact
- Inclusion and exclusion counts, plus the deduplication method
- Taxonomy and annotation-protocol versions
- Annotator count, adjudication method, and evaluation split strategy

A public URL does not automatically grant permission to republish its content. If terms do not permit storing full descriptions, retain only fields that are allowed and document the restriction. Do not describe a dataset as licensed or reviewed until those checks have actually been completed.

## 6. Evaluation design

- Deduplicate exact and near-duplicate postings before assigning splits.
- Group related postings by employer, source, or time period where possible so near duplicates do not leak between development and held-out sets.
- Use development records to refine taxonomy aliases. Freeze the rules before scoring the held-out set.
- Report per-role precision, recall, F1 and error labels, as well as micro and macro metrics.
- Include dataset size, taxonomy version, exclusions, known coverage gaps and limitations beside any score.
- Treat metrics as extraction performance on the documented dataset only. They do not establish labor-market trends or candidate suitability.

## 7. Release checklist

Before calling a benchmark empirical, confirm:

- [ ] Source and license/terms review are documented.
- [ ] Dataset manifest is complete and reproducible.
- [ ] IDs are unique, stable, and aligned with predictions.
- [ ] Duplicate and near-duplicate handling is documented.
- [ ] Annotation protocol and taxonomy versions are frozen.
- [ ] Every gold label has source-text evidence and ambiguous cases are recorded.
- [ ] Independent annotation and adjudication are recorded.
- [ ] Development and held-out split decisions are documented.
- [ ] No prohibited personal data or unlicensed text is committed.
- [ ] Results include error analysis and appropriately bounded conclusions.

Until these checks are complete, keep examples labeled as synthetic or exploratory and do not present their scores as empirical findings.
