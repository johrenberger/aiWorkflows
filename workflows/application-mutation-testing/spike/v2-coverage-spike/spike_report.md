# Spike Report: v2 → mutationctl coverage adapter

**Date:** 2026-06-13
**Author:** OpenClaw
**Status:** complete — green; one real gap surfaced (see §4)
**Recommendation:** ship as BDD story 019 in mutation (see §5)

## 1. What I built

A one-way data flow from `application-test-automation-v2` (test-factory)
to `application-mutation-testing` (mutationctl) at the **coverage ingest
boundary** (Phase 2 in mutation's workflow).

**Files added (115 lines of code, 0 deletions, 0 refactors):**

- `src/mutationctl/coverage/v2_risk_scores.py` (~95 lines) — new parser
- `tests/bdd/test_006b_v2_risk_scores_ingest.py` (~210 lines) — 13 tests
- `tests/fixtures/repos/v2_risk_scores_input/analysis-artifacts/risk_scores.json`
  (~40 lines) — fixture for the parser tests
- `src/mutationctl/coverage/ingest.py` — 2 surgical edits:
  - New `_candidate_paths()` helper with documented priority order
  - `ingest_coverage()` gains an optional `v2_artifact_path` parameter

**Files added (docs):**

- `spike/v2-coverage-spike/data_contract.md` — full data contract
- `spike/v2-coverage-spike/spike_report.md` — this file

## 2. What I verified

**Test counts:**

| Suite                                  | Tests | Pass | Fail | Skip |
|----------------------------------------|------:|-----:|-----:|-----:|
| `tests/bdd/test_006b_v2_risk_scores_*` |    13 |   13 |    0 |    0 |
| Full mutation test suite (regression) |   125 |  124 |    0 |    1* |

\* Pre-existing skip (`--randomly`-related, not related to this spike).

**End-to-end smoke test:**

Ran v2 against `/data/.openclaw/workspace/bdd-name-binary-app` with
`--out /tmp/v2-bdd-out`, then ran mutation's `ingest_coverage()`
pointing at that artifact:

```text
evidence_path: /tmp/v2-bdd-out/risk_scores.json
status: PASS
file count: 10
  backend/app/main.py:        line_cov=0.0  status=PASS  evidence=v2://backend/app/...
  frontend/src/api.js:        line_cov=0.0  status=PASS  evidence=v2://frontend/src/...
  backend/app/translation.py: line_cov=0.0  status=PASS  evidence=v2://backend/app/...
  ...
```

The `v2://` evidence prefix is the lineage marker that distinguishes
v2-sourced rows from rows sourced from `TODO_test-coverage.md` or
`coverage.xml`. mutation's existing ledger rendering code treats
`evidence_path` as opaque, so the prefix adds 7 chars per row without
breaking anything.

**Priority order verified by test:**

| Inputs                                          | Selected by ingest      | Test                        |
|-------------------------------------------------|-------------------------|-----------------------------|
| v2 + TODO + xml                                 | v2 (priority 1)         | `test_given_v2_and_todo..._v2_is_preferred` |
| TODO + xml (no v2)                              | TODO (priority 2)       | pre-existing test_006       |
| v2 only                                         | v2 (priority 1)         | `test_given_only_v2..._v2_is_used` |
| nothing                                         | NOT_RUN (priority 5)    | `test_given_no_coverage..._not_run` |
| external --out v2 + empty target repo            | external v2 (via parameter) | `test_given_external_v2_artifact...` |
| external --out v2 + in-repo v2                  | external (explicit wins) | `test_given_external_v2_artifact_and_in_repo_v2...` |

## 3. What the contract says (and why)

Full contract: `data_contract.md`. The short version:

- v2 emits per-file records with `path`, `line_coverage`, `branch_coverage`,
  `complexity`, `churn`, `module`, `language`, and other fields.
- mutation consumes the ones that fit its `target_score` formula:
  `path`, `line_coverage`, `branch_coverage`. The other v2 fields are
  ignored (mutation has no slot for `defect_history`,
  `public_api_exposure`, etc.).
- mutation does NOT consume v2's `risk_score` composite. Using it would
  be circular — mutation's own `target_score` is the authoritative
  ranking signal for *this* workflow.
- Priority order: v2 → TODO_test-coverage.md → coverage.xml → lcov →
  jacoco → internal fallback. v2 is highest because it's the most
  granular and the most recently authored.
- v2 is unaware of this contract. One-way data flow, additive only.

## 4. Real gap surfaced by the smoke test

The smoke test exposed a **real bug** in the spike — `CoverageFileSummary`
does not carry the per-file `complexity` value that v2 emits, even
though mutation's `target_score` formula uses it:

```python
def target_score(coverage: float, complexity: float) -> float:
    return round(
        0.35 * coverage
        + 0.25 * complexity   # <-- we need this
        + 0.20 * test_density_suspicion
        + 0.10 * runtime_feasibility
        + 0.10 * churn_or_default_priority,
        2,
    )
```

In the smoke test, all 10 files scored `33.25` because I had to pass
a placeholder `complexity=5.0` to `target_score()`. Without plumbing
v2's complexity through, mutation can't distinguish a high-complexity
file from a trivial one when using v2 as the source.

**This is exactly the kind of gap a spike is supposed to catch.** The
spike's job is to find the integration issues, not to ship a perfect
implementation. The gap is real, the fix is small, and the BDD story
can absorb it.

**Two ways to fix it (both in scope for story 019):**

1. **Extend `CoverageFileSummary`** to carry `complexity` (and optionally
   `churn` for the same reason). mutation's existing
   `complexity_score(source)` function would become a fallback when
   the v2 value is absent.
2. **Pass v2's raw record alongside** the `CoverageFileSummary`. The
   ledger can show "v2: complexity=12, churn=0" in addition to
   "mutation: target_score=42.0".

Option 1 is cleaner; option 2 is faster. Recommend option 1.

**Other gaps found:**

- **Stale-artifact detection.** v2's `risk_scores.json` could be
  hours/days old when mutation runs. The data contract doc flags this
  as a follow-up (Phase 2.5: compare v2 mtime to repo HEAD mtime,
  fall back if >24h gap). Not in this spike.
- **No `test_density` slot in v2.** v2's records don't directly
  expose a test-density signal. The default `50.0` in
  `test_density_suspicion` is fine for now.

## 5. BDD story 019 outline (mutation)

Title: `019_v2_risk_scores_ingest.md`

Acceptance scenarios:

1. Given a target repo with `analysis-artifacts/risk_scores.json` (v2 output)
   When mutation ingests coverage
   Then it consumes the v2 output, parses all per-file records, and
   uses `line_coverage` and `branch_coverage` directly.

2. Given a target repo with v2 output AND a `TODO_test-coverage.md`
   When mutation ingests coverage
   Then v2 wins (priority 1).

3. Given a target repo with no v2 output
   When mutation ingests coverage
   Then existing sources (TODO, xml, lcov, jacoco, fallback) work
   unchanged.

4. Given a v2 artifact in an external `--out` dir, specified via
   `--v2-artifact-path PATH`
   When mutation ingests coverage
   Then it consumes the external artifact.

5. Given a v2 record with `line_coverage=null` and
   `missing_evidence=["coverage"]`
   When mutation ingests coverage
   Then the per-file summary has `status="PARTIAL"`,
   `line_coverage=None`, and is still included in `target_score` with
   `coverage_readiness(line_coverage=None, fallback_allowed=True) → 40.0`.

6. **NEW** (gap from §4): Given a v2 record with `complexity=N`
   When mutation computes `target_score`
   Then it uses the v2-provided complexity, not a placeholder.

7. **NEW** (gap from §4): Given a v2 record with `complexity=null`
   When mutation computes `target_score`
   Then it falls back to mutation's internal `complexity_score(source)`.

Required executable tests (≥10):

- 4 parser-level tests on fixtures
- 3 priority-order tests
- 1 external-artifact-path test
- 1 in-repo vs external test
- 1 NOT_RUN fallback test
- 2 complexity-plumbing tests (new in this story)
- 1 ledger-rendering test that asserts the `v2://` evidence prefix
  appears in `TODO_mutation-testing.md`

Phases in mutation's workflow affected:

- Phase 2 ("Consume Coverage Context") — now reads v2 output
- Phase 4 ("Target Selection") — now has access to v2's complexity + churn
- Phase 9 ("Ledger Finalization") — evidence_path may have `v2://` prefix

Files to add/modify in mutation:

- **Add:** `stories/019_v2_risk_scores_ingest.md`
- **Add:** `src/mutationctl/coverage/v2_risk_scores.py` (already exists from this spike)
- **Add:** `tests/bdd/test_006b_v2_risk_scores_ingest.py` (already exists, expand with §6 + §7 tests)
- **Modify:** `src/mutationctl/coverage/ingest.py` (already has priority + v2_artifact_path)
- **Modify:** `src/mutationctl/models.py` (add `complexity: float | None` to
  `CoverageFileSummary`)
- **Modify:** `src/mutationctl/coverage/v2_risk_scores.py` (populate
  `complexity` from v2's record)
- **Modify:** `src/mutationctl/targeting/scorer.py` (or its caller) to
  use the new `complexity` field
- **Modify:** `TODO_mutation-testing.md` template (already in `reporting/`)
  to surface the `v2://` evidence prefix

Estimated scope: **1 working day** (story writing + implementation +
tests + ledger rendering + one end-to-end re-run on Broadleaf).

## 6. Time spent on the spike

- Reading both workflows end-to-end: ~20 min
- Running v2 on a real repo and capturing the shape: ~10 min
- Writing the data contract: ~25 min
- Implementing the parser: ~15 min
- Writing 11 tests: ~20 min
- Caught and fixed the JSON-as-XML bug: ~10 min
- Smoke test on real v2 output: ~5 min
- Surfacing and documenting the complexity gap: ~10 min
- **Total: ~2 hours.** Inside the half-day estimate from the analysis.

## 7. Bottom line

The spike works. The one-way data flow from v2 to mutation is
correct, additive, and well-tested. The 13 new tests give mutation
its first-class ability to consume v2's `risk_scores.json`, and the
end-to-end smoke against the BDD app proves the path works on real
data.

The complexity gap (v2 emits per-file complexity, mutation doesn't
currently plumb it through to `target_score`) is the only real
issue. It's a small fix, in scope for the BDD story.

**Recommendation: ship story 019.** Half-day to BDD, half-day to
implement + test, half-day to re-run Broadleaf through the new
path and capture before/after mutation scores. Total: 1.5 days.
Within the original 2-day estimate from the analysis.
