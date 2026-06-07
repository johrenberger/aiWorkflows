# Stage 13 — Test Execution Evidence (template)

The agent writes machine-readable results to
`artifacts/api_test_results.json`. This template is the human-readable
companion.

## Execution summary

| Metric | Count |
| --- | --- |
| executed | _n_ |
| passed   | _n_ |
| failed   | _n_ |
| skipped  | _n_ |
| errors   | _n_ |

## Commands run

_Sequential list with exit code and one-line outcome._

## Failures (one row per failure)

| Test | Endpoint | Failure class | One-line cause |
| --- | --- | --- | --- |

## Skips (one row per skip)

| Test | Reason |
| --- | --- |

## Blockers

_List any blockers that prevented execution._

## Environment

- API_BASE_URL:
- API_TOKEN source:
- Other env:
