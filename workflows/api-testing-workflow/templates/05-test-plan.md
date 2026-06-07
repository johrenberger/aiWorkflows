# Stage 6 — API Test Plan (template)

The agent writes the full plan to `artifacts/api_test_plan.md`. Use this
template to draft the per-endpoint matrix and the prioritization.

## Test categories

For each non-trivial endpoint, plan applicable tests:

```text
happy path
required field validation
invalid type validation
boundary value validation
malformed JSON
unsupported method
unauthorized request
invalid credentials/token
forbidden role/ownership boundary
not found behavior
duplicate create behavior
idempotency/retry behavior
pagination behavior
filter/sort behavior
response schema validation
error schema validation
content type validation
CORS behavior, if relevant
rate-limit behavior, if relevant and safe
```

## Per-endpoint plan (one row per endpoint)

| ID | Method | Path | Risk tier | Categories covered | Destructive? | Skip reason |
| --- | --- | --- | --- | --- | --- | --- |

## Prioritization

1. high-risk endpoints
2. auth/authz-sensitive endpoints
3. write / destructive endpoints (destructive tests disabled by default)
4. schema-heavy endpoints
5. endpoints with previous failures or drift

## Test markers

```python
@pytest.mark.api
@pytest.mark.contract
@pytest.mark.auth
@pytest.mark.security
@pytest.mark.destructive
@pytest.mark.slow
@pytest.mark.performance
@pytest.mark.resilience
```

## Notes

_Anything affecting test selection, e.g. missing test data, missing
deployed base URL, etc._
