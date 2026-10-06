# Workforce skill benchmark

This directory defines the structure for an annotated benchmark used to evaluate skill extraction.

Each record should contain a stable role identifier, source metadata, the raw job description, and a manually reviewed set of canonical skills. Source URLs or license/provenance notes should be retained outside the model input when redistribution is restricted.

## Required fields

- `role_id`: stable identifier
- `source`: dataset/source name
- `description`: job description text
- `gold_skills`: canonical skill names from the versioned taxonomy

## Evaluation rule

Compare extracted skills with `gold_skills` at the set level and report precision, recall, and F1. Keep the benchmark versioned so changes to the taxonomy do not silently change historical evaluation results.

The benchmark must use public, licensed, or synthetic data. Do not include personal candidate information.
