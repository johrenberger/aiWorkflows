# Stage 4 — Contract Normalization Evidence (template)

The agent writes the normalized contract to
`artifacts/openapi.normalized.yaml`. This template records how it was built
and what drift was found during normalization.

## Source

- Original spec location (file path or URL):
- Spec format (OpenAPI 2.0 / 3.0 / 3.1):
- Spec size (paths, schemas):

## Was the spec generated (inferred) or imported?

(imported | inferred | hybrid)

## Validation findings (against the spec)

- Invalid schema: yes | no — _details_
- Missing operation IDs: _count + list_
- Undocumented response codes: _count + list_
- Undocumented error shape: yes | no — _details_
- Missing auth definitions: yes | no — _details_
- Inconsistent parameter definitions: _count + list_
- Nullable / type mismatches: _count + list_
- Undocumented endpoints discovered in code: _count + list_
- Documented endpoints not found in implementation: _count + list_

## Inferred additions (only if the spec did not exist)

- Paths added: _count_
- Schemas added: _count_
- Comments / `x-inferred: true` markers added: yes | no

## Notes

_Anything a future run needs to know about why the contract looks the way
it does._
