# Stage 3 — API Inventory Evidence (template)

The agent writes the machine-readable inventory to
`artifacts/api_inventory.json`. This template is the human-readable companion
that summarizes the inventory for quick scanning.

## Discovery sources used

- [ ] OpenAPI/Swagger file or URL
- [ ] API route/controller/router files
- [ ] Existing integration/API tests
- [ ] Postman collections
- [ ] README/API documentation
- [ ] Frontend API client code
- [ ] Generated client SDKs
- [ ] Infrastructure configuration
- [ ] Deployed API safe probing
- [ ] Logs / examples / sample requests

## Endpoint count by risk tier

| Risk tier | Count |
| --- | --- |
| high   | _n_ |
| medium | _n_ |
| low    | _n_ |
| **total** | _n_ |

## High-risk endpoints (full list from inventory)

| ID | Method | Path | Source evidence | Inferred? |
| --- | --- | --- | --- | --- |

## Inferred endpoints (no source-of-truth documentation found)

| ID | Method | Path | Inference basis |
| --- | --- | --- | --- |

## Notes

_Anything the validator or the next run needs to know to interpret the
inventory correctly._
