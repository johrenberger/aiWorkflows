# Executive Report — Skill Governance Pipeline

- **Total skills:** 21
- **Total agents:** 0
- **Health score:** 69/100
- **CI status:** FAIL
- **Blocking findings:** 88
- **Warnings:** 120
- **Active waivers:** 0
- **Proposed rewrites:** 78
- **Benchmark results:** 0
- **Started:** 2026-06-13T23:44:13Z
- **Finished:** 2026-06-13T23:44:13Z

## Decisions
- **merge:** 64
- **rewrite:** 35

## Top risks
- `warning` **README**: Artifact 'README' is not a skill or agent (path: README.md). Skipping contract validation.
- `blocking` **SKILL**: Missing required metadata fields: name, artifact_type, purpose, category, owner, version, inputs, outputs, dependencies, intended_consumers, quality_level, last_reviewed
- `warning` **SKILL**: Purpose is missing or too short / vague.
- `blocking` **SKILL**: Inputs contract is missing or unstructured.
- `blocking` **SKILL**: Outputs contract is missing or unstructured.

## Recommended actions
- **merge** (architecture-risk-checklist): 0 blocking + 1 warnings on architecture-risk-checklist.
- **merge** (dotnet-testing): 0 blocking + 1 warnings on dotnet-testing.
- **merge** (architecture-review-report): 0 blocking + 1 warnings on architecture-review-report.
- **merge** (secrets-review-checklist): 0 blocking + 1 warnings on secrets-review-checklist.
- **merge** (incident-triage-report): 0 blocking + 1 warnings on incident-triage-report.

## Merge / split / rewrite / deprecate candidates

| Decision | Count |
| --- | --- |
| merge | 64 |
| rewrite | 35 |
