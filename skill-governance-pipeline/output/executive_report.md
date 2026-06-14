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
- **Started:** 2026-06-14T00:03:30Z
- **Finished:** 2026-06-14T00:03:30Z

## Decisions
- **rewrite:** 99

## Top risks
- `warning` **README**: Artifact 'README' is not a skill or agent (path: README.md). Skipping contract validation.
- `blocking` **SKILL**: Missing required metadata fields: name, artifact_type, purpose, category, owner, version, inputs, outputs, dependencies, intended_consumers, quality_level, last_reviewed
- `warning` **SKILL**: Purpose is missing or too short / vague.
- `blocking` **SKILL**: Inputs contract is missing or unstructured.
- `blocking` **SKILL**: Outputs contract is missing or unstructured.

## Recommended actions
- **rewrite** (release-gate-checklist): 1 blocking + 1 warnings on release-gate-checklist.
- **rewrite** (blocker): 1 blocking + 1 warnings on blocker.
- **rewrite** (task): 1 blocking + 1 warnings on task.
- **rewrite** (SKILL): 84 blocking + 42 warnings on SKILL.
- **rewrite** (adr): 1 blocking + 1 warnings on adr.

## Merge / split / rewrite / deprecate candidates

| Decision | Count |
| --- | --- |
| rewrite | 99 |
