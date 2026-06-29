# `.openclaw/dreaming/` — Nightly Dreaming Workflow Artifacts

This directory holds the artifacts produced by the `workflow-nightly-dreaming` cycle.

See `DREAMING.md` at the repo root for the entry point and full specification.

## Layout

| File | Purpose |
| --- | --- |
| `README.md` | This file |
| `workflow-nightly-dreaming.md` | Stage-by-stage execution spec for the workflow |
| `evidence-index.md` | Per-run evidence ledger; every recommendation traces here |
| `nightly-summary.md` | Concise evidence-backed run summary |
| `lessons-learned.md` | Compact, evidence-backed lessons (no vague lessons) |
| `failure-patterns.md` | Repeated, systemic, or one-off failure patterns |
| `success-patterns.md` | Successful patterns worth preserving or standardizing |
| `inefficiency-patterns.md` | Patterns that succeeded but with avoidable cost |
| `skill-usage-scorecard.md` | Skills scored 1–5 across required dimensions |
| `workflow-scorecard.md` | Workflows scored 1–5 across required dimensions |
| `regression-scenarios.md` | BDD-style Given/When/Then scenarios with pass/fail criteria |
| `minimax-consumption-brief.md` | Optional, manually-injected context pack for MiniMax |
| `proposed-improvements.md` | Proposed changes classified auto-safe / review-required / blocked |
| `pr-change-log.md` | Per-change audit trail with evidence reference |
| `validation-checklist.md` | Pre-merge validation checks |

## Constraints

- No section titled or starting with `Reasoning`, `Internal Analysis`, `Hidden Thoughts`, `Chain of Thought`, or `Private Reasoning`.
- No fenced `reasoning` blocks, no `<<<REASONING>>>` envelopes, no fenced blocks whose first line contains `reasoning`.
- Every recommendation, score, pattern, and proposed improvement must reference an evidence ID (`EV-####`).
- The MiniMax brief must not be referenced from prompts, agent spawn payloads, or default OpenClaw context.

## Version

- Cycle 1: 2026-06-29 (merged as PR #59)
- Cycle 2: 2026-06-29 cycle-2 (PI-008 applied; PR-review activity added as evidence source)
- Cycle 3: 2026-06-29 cycle-3 (post-merge `main` CI failure fixed; workflow trigger model documented as PI-011)
- Cycle 4: 2026-06-29 cycle-4 (PI-011 + PI-012 applied; maintenance cycle per P-S-005)
- Cycle 5: 2026-06-29 cycle-5 (PI-006 partial: spec + parser + parser tests; PI-006 status → `partial`)

## Local validation

Run `make dreaming-validate` (PI-008) to execute the same pytest suite as CI, locally, before pushing. See `validation-checklist.md` for the full pre-push gate.
