# Executive Report — Skill Governance Pipeline

- **Total skills:** 96
- **Total agents:** 21
- **Health score:** 0/100
- **CI status:** FAIL
- **Blocking findings:** 133
- **Warnings:** 2
- **Active waivers:** 0
- **Proposed rewrites:** 56
- **Benchmark results:** 0
- **Started:** 2026-06-13T22:26:05Z
- **Finished:** 2026-06-13T22:26:06Z

## Decisions
- **rewrite:** 126

## Top risks
- `blocking` **README**: Missing required metadata fields: name, artifact_type, purpose, category, owner, version, inputs, outputs, dependencies, intended_consumers, quality_level, last_reviewed
- `warning` **README**: Purpose is missing or too short / vague.
- `blocking` **README**: Inputs contract is missing or unstructured.
- `blocking` **README**: Outputs contract is missing or unstructured.
- `blocking` **README**: Outputs contract is vague (e.g. 'a report', 'analysis', 'summary').

## Recommended actions
- **rewrite** (skills/task-state-management): 1 blocking + 0 warnings on skills/task-state-management.
- **rewrite** (skills/validation-runner): 1 blocking + 0 warnings on skills/validation-runner.
- **rewrite** (skills/templates): 34 blocking + 0 warnings on skills/templates.
- **rewrite** (skills/test-gap-analysis): 2 blocking + 0 warnings on skills/test-gap-analysis.
- **rewrite** (approval-gate): 1 blocking + 0 warnings on approval-gate.

## Merge / split / rewrite / deprecate candidates

| Decision | Count |
| --- | --- |
| rewrite | 126 |
