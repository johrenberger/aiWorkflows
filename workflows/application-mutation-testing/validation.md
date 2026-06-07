# Application Mutation Testing Validation

## Required Validation Gates

- [ ] **MT-VAL-1 [Repository Input]** GitHub URL captured and repository cloned/opened.
- [ ] **MT-VAL-2 [Runtime Metadata]** Branch, commit, working tree, and timestamp recorded.
- [ ] **MT-VAL-3 [Mutation Tool Detection]** Mutation tool detected or blocker documented.
- [ ] **MT-VAL-4 [Target Selection]** Mutation targets selected with rationale.
- [ ] **MT-VAL-5 [Mutation Baseline]** Mutation run completed or blocker documented.
- [ ] **MT-VAL-6 [Survivor Classification]** Surviving mutants classified.
- [ ] **MT-VAL-7 [Hardening]** Tests strengthened where appropriate.
- [ ] **MT-VAL-8 [Focused Tests]** Focused tests pass or blocker documented.
- [ ] **MT-VAL-9 [Mutation Recheck]** Mutation recheck completed or blocker documented.
- [ ] **MT-VAL-10 [Ledger Complete]** `TODO_mutation-testing.md` includes all required sections.

## Mutation Score Policy

Initial target:

```text
>=60% mutation score
```

Mature target:

```text
>=75% mutation score
```

Do not enforce mature target as a first-run hard gate unless the repo already has strong coverage and mutation tooling.
