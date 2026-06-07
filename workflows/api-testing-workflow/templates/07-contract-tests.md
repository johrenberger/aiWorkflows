# Stage 8 — Contract and Compatibility Test Evidence (template)

The agent generates contract tests under `tests/contract/`. This template
records the contract test design and the drift findings.

## Tools used

- schemathesis: yes | no
- jsonschema (direct): yes | no
- pytest/httpx schema assertions: yes | no
- Pact / consumer-driven: yes | no

## Contract test files

| Path | Targets | Notes |
| --- | --- | --- |

## Drift findings (one row per finding)

| Endpoint | Method | Documented behavior | Actual behavior | Severity |
| --- | --- | --- | --- | --- |

## Undocumented 5xx responses detected

| Endpoint | Method | Trigger | Frequency |
| --- | --- | --- | --- |

## Backward-incompatible changes

_List with rationale and impact._

## Findings recorded in

`artifacts/api_defect_report.md` (this stage also seeds the defect report).
