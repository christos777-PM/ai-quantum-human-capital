# Prototype Evaluation Framework

This document defines how the technical prototype should be evaluated before stronger claims are made from workforce data.

## 1. Evaluation objectives

The prototype should answer four separate questions:
1. Extraction validity: Does the system identify skills that are actually present in the source text?
2. Coverage validity: Does the taxonomy represent the capability domains relevant to the research question?
3. Role-fit reliability: Does target-role comparison produce stable and interpretable results?
4. Management usefulness: Can the outputs support workforce-planning decisions without being mistaken for measures of individual competence?

These questions should be evaluated independently.

## 2. Evaluation objectives and baseline

The first benchmark should use a manually annotated sample of job descriptions. For each description, record the source identifier, role title, domain, explicitly stated skills, capability category, source/provenance, and annotator notes for ambiguous terms.

The rule-based extractor becomes the baseline system.

### Suggested metrics

**Precision** = true-positive extractions / all extractions.

Measures how often extracted skills are supported by the annotation.

**Recall** = true-positive extractions / all annotated skills.

Measures how much of the annotated skill set the extractor recovers.

**F1** = 2 × precision × recall / (precision + recall).

Provides a balance between precision and recall when both matter.

These metrics should be reported overall and by capability category where the sample is large enough.

## 3. Target-role evaluation

Target-role fit is currently calculated as:

coverage = matched required skills / required skills × 100

This is intentionally simple and transparent.

Evaluation should test whether required skills are correctly defined, whether extracted skills map to canonical terms, whether ranking remains deterministic, and whether small taxonomy changes cause understandable changes in results.

A coverage score must not be interpreted as employee competence, employability, performance probability, or hiring suitability.

## 4. Semantic-model comparison

Only after the deterministic baseline is stable should semantic methods be introduced.

A future experiment can compare rule-based extraction, embedding-based similarity, and LLM-assisted extraction against the same held-out annotations.

The comparison should report accuracy and operational characteristics such as reproducibility, explainability, computational cost, sensitivity to wording, and failure modes.

The objective is not to prove that a more complex model is automatically better. The objective is to establish whether additional complexity produces measurable research value.

## 5. Data quality and provenance

Every empirical dataset should document collection date, source, access method, license or permitted-use basis, inclusion/exclusion criteria, deduplication method, geography, time period, and known sampling limitations.

Synthetic or illustrative records must remain clearly separated from empirical observations.

## 6. Management interpretation

Results should be presented in three layers:

**Observed evidence:** What the dataset and model directly show.

**Interpretation:** What the observed pattern may indicate, including alternative explanations.

**Management implication:** What an organization could investigate or consider in response.

This separation prevents the analytical pipeline from turning a descriptive skill signal into an unsupported organizational recommendation.

## 7. Reproducibility standard

A result should be considered reproducible when another researcher can identify the dataset version, taxonomy version, analysis code version, configuration/target-role definition, command or procedure used, and resulting output.

This standard will be applied before empirical findings are used in the research conclusions.