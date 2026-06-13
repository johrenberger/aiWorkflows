# Spike: v2 → mutationctl coverage data contract

**Date:** 2026-06-13
**Author:** OpenClaw
**Status:** spike draft — pending validation

## Goal

Make `application-mutation-testing` (mutationctl) able to consume
`application-test-automation-v2` (test-factory) output as a
**first-class coverage source**, without changing v2's CLI or
mutation's core mutation logic.

The handoff is **one-way**: v2 emits, mutation consumes. mutation
still owns target selection, baseline, classification, hardening,
recheck, and commit.

## What v2 already produces (verified on bdd-name-binary-app)

Path: `<repo>/analysis-artifacts/risk_scores.json`

```json
[
  {
    "path": "backend/app/main.py",
    "module": "backend/app",
    "language": "python",
    "line_coverage": 0.0,
    "branch_coverage": null,
    "coverage_gap": 90.0,
    "complexity": 4.0,
    "churn": 0.0,
    "defect_history": 0.0,
    "public_api_exposure": 1.0,
    "data_or_security_sensitivity": 0.0,
    "dependency_fan_in": 7.0,
    "risk_score": 398.0,
    "missing_evidence": ["churn", "defect_history", "coverage"]
  },
  ...
]
```

**Per-record fields mutation needs and v2 provides:**

| v2 field                 | Type    | Used by mutation?            | Notes |
|--------------------------|---------|------------------------------|-------|
| `path`                   | string  | yes — `source_file`          | Relative to repo root, no leading `./` |
| `line_coverage`          | float   | yes — primary coverage input | 0–100 |
| `branch_coverage`        | float?  | yes — secondary              | Often `null` for non-coverage-bearing runs |
| `complexity`             | float   | yes — target_score `complexity` term | Numeric (0–100-ish) |
| `churn`                  | float   | yes — `churn_or_default_priority` term | Often 0 when git history not parsed |
| `module`                 | string  | yes — for `MutationTarget.module` | Optional in v2 |
| `language`               | string  | yes — for adapter dispatch   | "python" / "javascript" / "java" / "unknown" |

**v2 fields mutation does NOT need (and won't consume):**

- `risk_score` (composite, but mutation's target_score formula is
  authoritative — using v2's would be circular)
- `coverage_gap` (derived from line_coverage, redundant)
- `defect_history`, `public_api_exposure`, `data_or_security_sensitivity`,
  `dependency_fan_in` (interesting, but mutation's target_score has
  no slot for these — they'd be dead data unless we extend the formula)
- `missing_evidence` (informational only; mutation will treat missing
  fields as null/0 the same way it does for any other source)

**Per-record fields mutation needs that v2 does NOT provide:**

- `covered_lines: list[int]` — mutation's `CoverageFileSummary` has
  this field, but it's not used by `target_score`. Optional.
- `uncovered_lines: list[int]` — same, unused by scoring. Optional.
- These will be set to `[]` when consuming from v2, with a note in
  the ledger ("per-line data not available from v2 source").

## What mutation emits unchanged

`mutationctl` continues to emit `TODO_mutation-testing.md`,
`MT-VAL-*` gates, and the per-target record. The only thing that
changes is Phase 2's data source priority:

| Priority | Source                       | When used |
|----------|------------------------------|-----------|
| 1        | v2 `risk_scores.json`        | When `analysis-artifacts/risk_scores.json` exists |
| 2        | `TODO_test-coverage.md`      | When v2 output absent and todo file present |
| 3        | `coverage.xml` / `lcov.info` / `jacoco.xml` | When v2 + todo absent and one of these exists |
| 4        | Internal fallback            | No coverage source at all — `coverage_readiness` returns 40.0 with `fallback_allowed=True` (current default) |

Priority 1 is a one-way data flow — it does not require v2 to know
that mutation exists. mutation does the discovery.

## Field mapping v2 → mutationctl

```python
def v2_record_to_mutation_summary(rec: dict) -> CoverageFileSummary:
    return CoverageFileSummary(
        source_file=rec["path"],
        line_coverage=rec.get("line_coverage"),
        branch_coverage=rec.get("branch_coverage"),
        covered_lines=[],   # v2 doesn't expose per-line data
        uncovered_lines=[], # same
        evidence_path=f"v2://{rec.get('module', 'unknown')}/risk_scores.json",
        status="PASS" if rec.get("line_coverage") is not None else "PARTIAL",
    )
```

The `evidence_path` prefix `v2://` is a stable marker so the ledger
can attribute the source. mutation's existing ledger code already
treats `evidence_path` as opaque; the prefix adds 7 chars per row.

## Target scoring: does the formula need to change?

**No.** mutation's `target_score` formula is:

```
0.35 * coverage + 0.25 * complexity + 0.20 * test_density +
0.10 * runtime + 0.10 * churn
```

v2 provides `coverage` (`line_coverage`) and `complexity` and
`churn` directly. The other two terms (`test_density`,
`runtime_feasibility`) keep their current default values:

- `test_density_suspicion = 50.0` — same default
- `runtime_feasibility = 100.0` — same default

**Optional future change (not in scope of this spike):**
v2's `dependency_fan_in` and `public_api_exposure` are signals that
mutation's formula ignores. A future BDD story could add a
`module_centrality` term weighted at 0.05, reducing `churn` weight
to 0.05. That's a separate spec change and shouldn't ship with the
data contract.

## What mutation gains from this

1. **Better target selection on real codebases.** v2's `risk_score`
   is a strong prior on which files to mutation-test. mutation's
   internal `target_score` will see the same `coverage` and
   `complexity` it would have computed itself, but the lineage
   through v2's pipeline means mutation's selection is now
   reproducible from `analysis-artifacts/` (one less re-run needed
   if the user has already run v2).
2. **Cleaner Phase 2 / Phase 4 boundary.** Today, mutation's
   Phase 2 reads `TODO_test-coverage.md` (a human-authored
   ledger). v2's `risk_scores.json` is machine-authored, more
   granular, and updated on every run. For a fresh codebase, the
   v2 source is strictly better.
3. **No regression for v2-less repos.** The priority table above
   keeps the existing four sources working as before. The only
   behavior change is: if a repo has BOTH a `TODO_test-coverage.md`
   AND a `analysis-artifacts/risk_scores.json`, mutation will now
   prefer v2. The v2 source has higher fidelity (per-file
   complexity + churn), so this is the right call, but it should
   be called out in the BDD story.

## What mutation does NOT gain

1. Survivor classification. mutation still owns this end-to-end.
   v2's `risk_score` is a target-selection signal, not a
   survivor-classification signal. Different problem.
2. Mutation tool detection. mutation owns the
   Python/JS/Java detection logic in `detection/`. v2 also has
   detection in `adapters/*`, but with different rules. Do not
   unify.
3. Test patch safety. mutation owns
   `mutationctl.patches.conservative_diff`. v2 has nothing here.
4. Commit / branch safety. mutation owns
   `mutationctl.git.commit_planner`. v2 has its own
   `branch`/`commit` subcommands with different defaults. Do not
   unify.
5. LLM survivor classification. mutation's `llm/` package is
   a fake-LLM contract test surface today. v2's `mutate` does
   not call LLMs. Coupling them would force v2 to grow an
   LLM-policy module it doesn't need.

## Cost to implement (this spike only)

- 1 new parser file: `coverage/v2_risk_scores.py` (~50 lines)
- 1 new test file: `tests/bdd/test_006b_v2_risk_scores_ingest.py` (~60 lines, fixture-driven)
- 1 line change to `coverage/ingest.py`: add v2 path to candidate list
- 1 line change to ledger rendering: detect `v2://` prefix and note source
- **Total: ~115 lines, all additive. No deletions, no refactors.**

The full v2 data contract is documented in this file; the BDD
story 019 in mutation will reference it.

## Open questions

1. **Should v2 be told about this contract, or is it one-way?**
   Recommendation: one-way. v2 is a general-purpose test-coverage
   factory; it shouldn't grow awareness of every consumer. The
   contract is the v2 artifact's shape, which is already
   documented. mutation is just another reader.

2. **What if v2's `risk_scores.json` is stale (e.g. v2 was run a
   week ago and the repo has changed)?** mutation's Phase 1
   already records `commit, branch, working tree, timestamp`. We
   should add a Phase 2.5 step that checks the v2 artifact's
   mtime against the repo's HEAD commit mtime, and falls back to
   TODO_test-coverage.md if the gap is >24h. Not in this spike —
   it's a follow-up BDD story.

3. **What if v2 emits `missing_evidence: ["coverage"]` for a file?**
   That means v2 couldn't get coverage data for it. mutation
   should treat `line_coverage=None` exactly as it does today
   (via `coverage_readiness(fallback_allowed=True) → 40.0`). The
   status field in `CoverageFileSummary` becomes `PARTIAL` (already
   supported). No code change needed beyond the parser.

4. **What about v2's per-module granularity?** v2 groups files by
   `module`; mutation's `MutationTarget` has its own `module`
   field. The mapping is direct — pass `module` through.

5. **Will this break the existing `test_006_coverage_ingestion.py`?**
   No. The new parser is added to the candidate list; the existing
   tests don't assert order, they assert that a given input file
   produces the right summary. New tests will assert the v2 case.

## Recommendation

Ship this spike as BDD story 019 in mutation. Half-day to
implement + test, half-day to validate end-to-end on a fresh repo
(focus_converters is a good candidate — small, Python, has tests).
Total: 1 day. Same as Option A from the analysis, but with the
specific scope now pinned to "v2 → mutation, one-way, additive
only."
