# Stage 7 — Functional Test Generation Evidence (template)

The agent generates the actual tests under `tests/api/`. This template
records the test design decisions so a future run can match them.

## Test stack used

- pytest:
- httpx:
- jsonschema:
- pydantic:
- schemathesis:
- pytest-html:
- pytest-xdist:
- other:

## Fixtures

- `tests/api/conftest.py` responsibilities:
- `tests/api/client.py` responsibilities:

## Environment variables consumed

```text
API_BASE_URL
API_TOKEN
API_USERNAME
API_PASSWORD
API_KEY
```

## Markers registered

(`api`, `contract`, `auth`, `security`, `destructive`, `slow`, `performance`,
`resilience`)

## Test files generated

| Path | Endpoints covered | Markers used |
| --- | --- | --- |

## Determinism

- Test data generation: _how are unique IDs produced_
- Resource cleanup: _how are created resources torn down_
- Order dependence: _none | explained_

## Notes

_Anything affecting test execution later, e.g. known-skip endpoints,
required env vars that are missing in this run._
