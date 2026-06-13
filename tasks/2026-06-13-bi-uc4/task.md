# Use case #4: POST endpoint with validation (WITH backend-implementation skill)

## Goal

Add a new POST endpoint that creates a pet with a new
owner in a single request. Validate inputs (required
fields, types, dates) and return appropriate 400 errors.

## Endpoint

`POST /api/pets-with-owner`

Request body:
```json
{
  "ownerFirstName": "John",
  "ownerLastName": "Doe",
  "ownerAddress": "123 Main St",
  "ownerCity": "Springfield",
  "ownerTelephone": "5551234567",
  "petName": "Buddy",
  "petBirthDate": "2020-01-01",
  "petTypeId": 2
}
```

Returns:
- 201 Created with the new pet's URI
- 400 Bad Request if validation fails
  (missing required fields, invalid date, etc.)

## Acceptance criteria

1. POST endpoint exists and creates both Owner and Pet
2. Required field validation: owner first name, last name,
   telephone; pet name, birth date, type
3. Invalid date format returns 400
4. Non-existent pet type id returns 400
5. New tests: at least 2
6. All 237 baseline tests must still pass

## Methodology

Follow the `backend-implementation` skill workflow:
- profile: java-spring
- 7 steps: discovery gate, backend ownership, inspect
  patterns, tests, implement smallest safe change,
  validation-runner, handoff packet
