# Component Test Analysis Workflow

**Purpose:** Generate a deep, structured **analysis** of a GitHub repository's component-level testing strategy. **Read-only by intent** — this workflow does not write tests, run tests, or modify the target repo. Its output is a machine-readable spec that downstream workflows (e.g. `application-test-coverage`, `application-mutation-testing`) consume.

**Origin:** Reformatted from a 28-section analysis prompt into a deterministic workflow with tiered profiles. Lives at `workflows/component-test-analysis/`.

## When to use

Use this workflow when you want to:
- **Audit a repo's testing strategy** before deciding what to improve.
- **Build a gap backlog** to feed into `application-test-coverage` (it can use the `gap-backlog.json` directly).
- **Define test architecture** for a new project (component boundaries, decision tree, fidelity strategy).
- **Generate input for an AI-driven test-generation system** (the spec's section 24 schema is exactly that).

Do **not** use this workflow to:
- Write tests (use `application-test-coverage`).
- Measure test effectiveness via mutation (use `application-mutation-testing`).
- Discover the repo at a high level (use `app-dev-discovery` — this is a focused subset of that workflow's concerns, plus testing-specific).

## Profile tiers

The workflow supports three depth profiles, encoded as `ANALYSIS_PROFILE` input:

| Profile | Sections | Wall-clock (rough) | Output |
|---|---|---|---|
| **LITE** | 1, 2, 4, 7, 8, 9, 13, 26 | 10-20 min | Repository analysis + component inventory + behavioral coverage + current coverage assessment + gap backlog + coverage strategy + rollout plan. The "I need to make a decision tomorrow" profile. |
| **STANDARD** (default) | LITE + 3, 5, 6, 11, 14, 15, 21, 27 | 30-60 min | + Dependency risk + dataset integrity + state transitions + contract coverage + test fidelity + decision tree + risk priority ranking + quality gates. The "I'm planning a quarter" profile. |
| **FULL** | All 28 sections | 2-4 hours | Every section. The "I'm writing the strategy doc" profile. |

See `_docs/profile-tiers.md` for the per-section mapping and what each tier skips.

## Outputs

**Always produced** (regardless of profile):
- `TODO_component-analysis.md` — the human-readable ledger (Markdown).
- A subset of 8 JSON artifacts (see `output-template.md`) — **only those whose source data was actually found** in the repo. Empty JSONs are not emitted; downstream consumers must check existence, not assume a fixed set.

**Per profile**, the JSONs produced are:

| JSON | LITE | STANDARD | FULL |
|---|:---:|:---:|:---:|
| `component-inventory.json` | ✅ | ✅ | ✅ |
| `behavior-coverage.json` | ✅ | ✅ | ✅ |
| `gap-backlog.json` | ✅ | ✅ | ✅ |
| `dependency-risk-matrix.json` | — | ✅ | ✅ |
| `state-transition-matrix.json` | — | ✅ | ✅ |
| `contract-inventory.json` | — | ✅ | ✅ |
| `risk-priority-ranking.json` | — | ✅ | ✅ |
| `mutation-roadmap.json` | — | — | ✅ |

## Handoffs

- **To `application-test-coverage`:** `gap-backlog.json` + `component-inventory.json` can be loaded as `MODULE_LIST` and the targeted picks list. See `_docs/handoffs.md` for the exact translation.
- **To `application-mutation-testing`:** `mutation-roadmap.json` (FULL profile only) defines targets and exclusions.
- **To AI test-generation systems:** Section 24 of the original prompt defines a machine-readable schema for test-creation workflow input. The workflow emits this as `test-creation-input-schema.json` (FULL profile only).

## Inputs

See `workflow.md` for the full input contract. The minimum is:

```text
INPUT_GITHUB_REPO=<github-url>
INPUT_BRANCH=<optional branch>
ANALYSIS_PROFILE=lite|standard|full  # default: standard
```

## Files

- `workflow.md` — objective, inputs, phases, handoff contracts.
- `prompt-implementation.md` — the executor prompt.
- `output-template.md` — the Markdown ledger template + JSON schema docs.
- `validation.md` — quality gates and TC-VAL-* checks.
- `recovery.md` — interruption and repair patterns.
- `_docs/profile-tiers.md` — per-section profile mapping.
- `_docs/handoffs.md` — explicit handoff contracts to coverage / mutation workflows.
