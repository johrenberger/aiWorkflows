# Stages 10–12 — Performance, Resilience, Observability Evidence (template)

The agent writes the full content to:

- `artifacts/api_performance_plan.md`
- `artifacts/api_resilience_plan.md`
- `artifacts/api_observability_recommendations.md`

This template captures the decisions and findings across all three stages so
the next run has the context.

## Performance (Stage 10)

- Enabled: yes | no
- Scenarios covered: baseline | ramp | spike | stress | soak | recovery
- Tooling: k6 | locust | pytest-benchmark | hey | wrk | other
- Execution: not performed (plan only, by default)
- Threshold source: project SLOs | recommended starting points

## Resilience (Stage 11)

- Enabled: yes | no
- Chaos enabled: yes | no
- Scenarios covered: _list_
- Safety constraints observed: _list_

## Observability (Stage 12)

- Current observability evidence: _summary_
- Missing telemetry: _list_
- Recommended metrics: _list_
- Recommended logs: _list_
- Recommended traces: _list_
- Recommended alerts: _list_
- Dashboard outline: _bullets_

## Notes

_Anything affecting future runs._
