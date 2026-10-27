# AI & Quantum Human Capital

Research repository for **Human Capital Transitions in the Computational Industry: Connecting the Impacts of Artificial Intelligence and Quantum Computing in India**.

The repository is being developed alongside the technical prototype in [AI Workforce Intelligence](https://github.com/christos777-PM/ai-workforce-intelligence).

## Research question

**How can organizations prepare people for computational technologies that are changing faster than traditional workforce-planning models?**

## Scope

The research examines the human-capital implications of:

- Artificial Intelligence and generative AI
- Quantum computing and the emerging quantum ecosystem
- Skills and competency transitions
- Workforce readiness and reskilling
- Organizational change
- The relationship between technology adoption and human-capital strategy
- India's emerging technology and semiconductor ecosystem

## Conceptual foundations

The working theoretical lens combines:

1. **Human Capital Theory** — skills, education and capability as forms of productive human capital.
2. **Socio-Technical Systems Theory** — technology, people and organizational structures as an interacting system.
3. **Change Management** — how organizations move from current capabilities toward future-state workforce readiness.

## Research → prototype connection

This repository contains the research framing, while the companion technical project turns one part of the research problem into a reproducible pipeline:

```
Research question
      ↓
Literature & theory
      ↓
Workforce capability questions
      ↓
Job-role data
      ↓
AI Workforce Intelligence prototype
      ↓
Skills evidence
      ↓
Management implications
```

## Current research artifacts

- Research question and scope
- Theoretical framework
- Literature-review workspace
- Workforce capability taxonomy
- Technical prototype linkage
- A reproducible benchmark evaluator for skill-extraction predictions

## Benchmark evaluation

A small, synthetic JSONL benchmark demonstrates how skill-extraction predictions can be evaluated without presenting invented examples as labor-market evidence.

Run the example from the repository root:

```bash
python scripts/evaluate_benchmark.py \
  --gold data/benchmark/example.jsonl \
  --predictions data/benchmark/example_predictions.jsonl \
  --output /tmp/benchmark-report.json
```

The evaluator reports per-role precision, recall and F1 with explicit matched, false-positive and false-negative skill labels, plus micro metrics and macro F1. Skill labels are compared as case-insensitive exact-match sets after trimming whitespace. It deliberately does not infer synonyms or semantic equivalence. The benchmark format, metric definitions and limitations are documented in [the benchmark README](data/benchmark/README.md).

### End-to-end companion integration

The repository also includes a smoke-test runner that calls the installed `workforce-intel` CLI, consumes its JSONL predictions, and passes them to the evaluator:

```bash
python -m pip install -e ../ai-workforce-intelligence
python scripts/run_workforce_demo.py \
  --jobs-csv ../ai-workforce-intelligence/data/sample_jobs.csv \
  --gold data/benchmark/workforce_demo_gold.jsonl \
  --output /tmp/workforce-demo-report.json
```

The integration workflow checks out the companion repository and runs this path in CI. The five-role fixture exercises common plural forms handled by the companion's explicit alias map and retains one intentional abbreviation miss: `AI` is not yet normalized to the canonical `artificial intelligence` label. The pinned scores are regression checks for this synthetic fixture only, **not** evidence of real-world extractor quality.

**Important:** all bundled records are synthetic smoke-test data, not a representative sample, a model-quality claim, or evidence about the Indian workforce. Empirical conclusions require a documented, appropriately licensed dataset and a manually reviewed annotation protocol.

## Research discipline

This repository is intended for academic and exploratory work.

Findings should be grounded in documented sources and clearly separated into:

- **Observed evidence**
- **Interpretation**
- **Research limitations**
- **Implications for organizations**

The technical prototype uses synthetic/illustrative data unless a dataset is explicitly documented as public and appropriately licensed. Do not include personal candidate information.

## Planned work

- [ ] Literature review matrix
- [ ] Scopus search strategy and inclusion criteria
- [ ] Theoretical framework diagram
- [ ] Workforce-transition conceptual model
- [ ] Karnataka/Bengaluru case context
- [ ] Licensed/public job-data collection
- [ ] Empirical analysis
- [ ] Validation of the capability taxonomy
- [ ] Human-reviewed benchmark labels using a documented protocol
- [x] Synthetic integration smoke test connecting the rule-based extractor to transparent evaluation
- [ ] Held-out evaluation using a licensed dataset and human-reviewed reference labels
- [ ] Research findings and management implications

## Companion project

**[AI Workforce Intelligence](https://github.com/christos777-PM/ai-workforce-intelligence)**

The companion project provides the executable technical layer: Python package, taxonomy, skill extraction, analysis, tests and CI.

---

This repository is a working research artifact. Methods and conclusions will evolve as the literature review and empirical evidence develop.
