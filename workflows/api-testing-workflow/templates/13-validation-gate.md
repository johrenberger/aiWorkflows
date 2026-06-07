# Stage 16 — Validation Gate (template)

The runner's `validate.sh` enforces the gate mechanically. The agent should
self-check using this list before reporting success, and write a record of
the self-check here.

## Artifacts

- [ ] `artifacts/api_testing_context.md`
- [ ] `artifacts/api_inventory.json`
- [ ] `artifacts/openapi.normalized.yaml`
- [ ] `artifacts/api_test_plan.md`
- [ ] `tests/api/`
- [ ] `artifacts/api_security_findings.md`
- [ ] `artifacts/api_performance_plan.md`
- [ ] `artifacts/api_resilience_plan.md`
- [ ] `artifacts/api_observability_recommendations.md`
- [ ] `artifacts/api_test_results.json`
- [ ] `artifacts/api_defect_report.md`
- [ ] `artifacts/api_change_log.md`
- [ ] `artifacts/api_workflow_summary.md`
- [ ] `TODO_api-tester.md`

## Safety gates

- [ ] no secrets in artifacts
- [ ] failures were triaged
- [ ] skipped tests include reasons
- [ ] destructive tests were not run unless allowed
- [ ] performance / chaos tests were not run unless allowed

## Validation result

PASS | FAIL — _one-line summary_
