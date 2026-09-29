# Research-to-Prototype Methodology

## Purpose

This document defines how the **AI & Quantum Human Capital** research repository connects its academic research question to the executable **AI Workforce Intelligence** prototype.

The goal is to prevent the technical system from becoming a disconnected software demo. Each computational output should answer a defined workforce-research question and each research claim should identify the evidence needed to support it.

## 1. Research question

> How can organizations prepare people for computational technologies that are changing faster than traditional workforce-planning models?

The technical prototype addresses one operational slice of this question:

> What capability signals appear in emerging-technology roles, and how can those signals be compared with a defined target-role capability profile?

## 2. Conceptual chain

```
Technology transition
       ↓
Changing work requirements
       ↓
Emerging role descriptions
       ↓
Observed skills
       ↓
Capability categories
       ↓
Target-role capability profile
       ↓
Coverage and skill gaps
       ↓
Workforce-development implications
```

This chain separates **observation** from **interpretation**. The prototype can identify text-based skill signals; it cannot by itself establish that a skill is economically valuable, difficult to hire for, or causally responsible for workforce outcomes.

## 3. Research concepts mapped to the prototype

| Research concept | Prototype representation | Evidence produced |
|---|---|---|
| Human capital | Skills and capability requirements | Extracted skill signals |
| Technological change | AI, cloud, semiconductor, embedded and systems roles | Role corpus |
| Workforce readiness | Target-role coverage | Coverage percentage |
| Skills transition | Required skills absent from observed roles | Skills-gap output |
| Socio-technical systems | Technical + project/system capability categories | Capability taxonomy |
| Organizational change | Target-state capability profile | Explicit target definition |

## 4. Analytical units

The current prototype uses three units:

### Role

A job description represented by:

- `title`
- `description`

### Skill

A canonical phrase from the versioned capability taxonomy, such as:

- Python
- machine learning
- AWS
- project management
- systems engineering

### Target capability profile

A declared set of skills representing a role or future-state capability requirement.

The target profile is **not** a claim that every organization uses the same requirements. It is an explicit analytical assumption that can be changed and evaluated.

## 5. Measurement logic

### Skill extraction

The baseline extractor performs deterministic whole-word or phrase matching against a versioned taxonomy.

This provides:

- reproducibility
- traceability
- easy debugging
- a baseline for evaluating future semantic or LLM-based approaches

### Coverage

For required skill set **R** and observed skill set **P**:

```
Coverage = |R ∩ P| / |R| × 100
```

A coverage score therefore measures **observable skill overlap**, not competence.

### Role fit

For each observed role, the prototype calculates:

- coverage percentage
- matched skills
- missing skills

Roles are ranked by descending coverage. Equal scores are ordered alphabetically to make output deterministic.

## 6. What the prototype can and cannot establish

### It can support

- descriptive analysis of job-description language
- comparison of role capability profiles
- identification of recurring capability categories
- transparent skills-gap calculations
- reproducible baseline experiments

### It cannot establish on its own

- employee proficiency
- labor-market scarcity
- salary effects
- causal effects of AI or quantum computing
- organizational performance
- whether a skill is genuinely more important than another skill
- future demand without an appropriate longitudinal dataset

These boundaries are important because job descriptions are organizational artifacts, not direct measurements of human capability.

## 7. Evaluation plan

Future versions should be evaluated in stages.

### Stage 1 — Baseline correctness

Measure whether deterministic extraction matches a manually labelled sample.

Suggested metrics:

- precision
- recall
- F1 score
- category-level confusion analysis

### Stage 2 — Semantic matching

Compare the deterministic baseline with an embedding-based approach.

The comparison should report both:

- cases where semantic matching improves recall
- cases where semantic matching introduces false positives

### Stage 3 — LLM-assisted extraction

If an LLM is introduced, it should be evaluated against the same labelled benchmark rather than treated as inherently more accurate.

The experiment should record:

- model/version
- prompt/version
- taxonomy version
- dataset version
- evaluation metrics
- representative errors

### Stage 4 — Research validity

Only after measurement validity is established should the analysis be used to support broader claims about workforce transitions.

## 8. Data discipline

The project should prefer:

1. public datasets with clear licensing;
2. synthetic data for software-development tests;
3. documented provenance for every empirical dataset.

Each empirical dataset should eventually record:

- source
- collection date
- geographic scope
- occupational scope
- licensing/usage terms
- preprocessing steps
- exclusions
- known sampling limitations

Personal candidate data should not be used.

## 9. Reproducibility contract

A published analysis should be reproducible from:

**dataset version + taxonomy version + code version + analysis configuration**

This means future experiments should avoid silently changing the taxonomy or preprocessing rules.

## 10. Management interpretation

The intended management output is not simply a list of technologies.

A useful interpretation should move through four levels:

**Observed:** What skills appear in the data?

**Pattern:** Which capability categories recur across roles?

**Gap:** Which capabilities are absent from a defined target profile?

**Action:** What workforce-development intervention could address the gap?

Possible interventions include:

- structured upskilling
- targeted hiring
- cross-functional team formation
- internal mobility
- external partnerships
- role redesign

The final intervention should always be treated as a management decision informed by evidence, not as an automatic output of the model.

## 11. Current prototype boundary

The companion project currently uses a small synthetic/illustrative dataset.

Therefore, current outputs demonstrate **method feasibility**, not empirical conclusions about India's labor market.

The next research milestone is a documented public/licensed dataset followed by manual annotation and baseline evaluation.

## Companion implementation

The executable implementation is maintained in:

**[AI Workforce Intelligence](https://github.com/christos777-PM/ai-workforce-intelligence)**

The two repositories should evolve together:

```
Research framing
      ↕
Measurement design
      ↕
Technical implementation
      ↕
Evaluation
      ↕
Empirical findings
      ↕
Management implications
```
