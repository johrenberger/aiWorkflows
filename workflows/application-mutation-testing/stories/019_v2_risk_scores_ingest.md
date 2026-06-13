# Story 019: V2 Risk Scores Ingest

## Goal

As the workflow, I need to consume `application-test-automation-v2`
(test-factory) output as a first-class coverage source so that mutation
target selection benefits from v2's per-file complexity, churn, and
risk signals — without coupling the two workflows.

## Background

The data contract is documented in
`spike/v2-coverage-spike/data_contract.md`. The one-way data flow is:

```
v2 (test-factory)  --emits-->  analysis-artifacts/risk_scores.json
                                       |
                                       v
mutationctl.coverage.ingest  --reads-->  CoverageFileSummary (with v2 complexity)
                                       |
                                       v
mutationctl.targeting.selector  --uses-->  target_score
```

v2 is unaware of this contract. The integration lives entirely in
mutationctl.

## Acceptance Scenarios

1. **v2 artifact is consumed at highest priority.**
   Given a target repo with `analysis-artifacts/risk_scores.json` (v2 output)
   When mutation ingests coverage
   Then it consumes the v2 output, parses all per-file records, and
   uses `line_coverage`, `branch_coverage`, and `complexity` directly.

2. **v2 wins over TODO_test-coverage.md when both exist.**
   Given a target repo with v2 output AND a `TODO_test-coverage.md`
   When mutation ingests coverage
   Then v2 wins (priority 1 in the documented order).

3. **Existing sources still work when v2 is absent.**
   Given a target repo with no v2 output
   When mutation ingests coverage
   Then existing sources (TODO, xml, lcov, jacoco, fallback) work
   unchanged (priority 2-5).

4. **External v2 output dir is supported.**
   Given a v2 artifact in an external `--out` dir, specified via
   `--v2-artifact-path PATH`
   When mutation ingests coverage
   Then it consumes the external artifact.

5. **Records with null coverage are still included as PARTIAL.**
   Given a v2 record with `line_coverage=null` and
   `missing_evidence=["coverage"]`
   When mutation ingests coverage
   Then the per-file summary has `status="PARTIAL"`,
   `line_coverage=None`, and is still included in `target_score` with
   `coverage_readiness(line_coverage=None, fallback_allowed=True) → 40.0`.

6. **Per-file complexity from v2 is used by target_score.**
   Given a v2 record with `complexity=N` (N != null)
   When mutation computes `target_score`
   Then it uses the v2-provided complexity, not a placeholder.

7. **Null complexity falls back to mutation's internal scorer.**
   Given a v2 record with `complexity=null`
   When mutation computes `target_score`
   Then it falls back to `complexity_score(source)`.

## Executable Test Mapping

`tests/bdd/test_006b_v2_risk_scores_ingest.py` — 16 tests covering scenarios 1-7.

`tests/bdd/test_019b_stale_v2_artifact_falls_back.py` — open 3 (stale-artifact detection).

`tests/bdd/test_019c_ledger_surfaces_v2_prefix.py` — open 2 (ledger rendering).

## Done Criteria

- v2 priority is deterministic (priority 1 in `coverage/ingest.py`).
- All v2 fields mutation consumes are populated on `CoverageFileSummary`.
- Null coverage and null complexity are handled gracefully (PARTIAL status,
  fallback to `complexity_score(source)`).
- External v2 output dir is supported via `v2_artifact_path` parameter.
- Ledger rendering surfaces the `v2://` evidence prefix.
- Stale v2 artifacts (mtime > 24h vs repo HEAD) fall back to the next
  available source.
- End-to-end smoke against a real repo (metabase or focus_converters)
  confirms the integration.
