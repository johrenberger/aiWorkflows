# Stage 17 — Workflow Summary (template)

The agent writes the full summary to `artifacts/api_workflow_summary.md`
and a human-readable rollup to `docs/api-testing-<yyyy-mm-dd>.md`.

## Sections (one section per bullet — keep concise)

- Execution mode
- Target details
- API surface summary
- Contract source
- Tests generated
- Tests executed
- Results summary
- Highest-risk findings
- Security findings summary
- Performance readiness summary
- Resilience readiness summary
- Observability recommendations summary
- Files created
- Files changed
- Commands run
- Blockers
- Assumptions
- Recommended next actions

## Human-readable rollup (`docs/api-testing-<yyyy-mm-dd>.md`)

The rollup must contain, in this order:

1. 1-paragraph executive summary
2. Execution mode + target details
3. API surface summary (counts by risk tier)
4. Highest-risk findings (top 5)
5. Test results summary
6. Security findings summary
7. Performance / resilience / observability readiness (one line each)
8. Drift from previous run (or "baseline run")
9. Recommended next actions
10. Paths to the full evidence directory and the task tracker
