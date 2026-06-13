# Task: 2026-06-13-fi-stack

## Goal

Exercise the `frontend-implementation` skill against a
React 18 + Vite UI for the PetClinic proxy. Promote the
skill from `draft` to `usable` on the strength of 3 use
cases.

## Use case plan

| # | Description | Skill |
|---|---|---|
| UC1 | PetVisitList component (fetches + renders) | ❌ no skill (baseline) |
| UC2 | NewVisitForm with client-side validation, a11y | ✅ with skill |
| UC3 | PetTypeFilter combobox with debounced search, ARIA | ✅ with skill |

## Stack

- React 18
- Vite 5
- Vitest 2 + @testing-library/react 16 + jest-axe 9
- Plain CSS (no framework)
- Target: PetClinic Node proxy on `localhost:3001`

## Repo

- New project at `johrenberger/petclinic-ui` (NOT yet created)
- Will be re-baselined to remove any upstream links
