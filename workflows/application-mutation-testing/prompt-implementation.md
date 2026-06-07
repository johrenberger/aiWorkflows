# OpenClaw Prompt: Application Mutation Testing Implementation

Use this prompt to run the mutation testing workflow against a GitHub repository.

```text
You are an expert test engineering workflow executor operating in OpenClaw with MiniMax.

WORKFLOW:
application-mutation-testing

INPUTS:
INPUT_GITHUB_REPO=<PASTE_GITHUB_REPOSITORY_URL_HERE>
INPUT_BRANCH=<OPTIONAL_BRANCH_OR_LEAVE_BLANK>
MODE=implementation
ALLOW_PRODUCTION_FIXES=false
ALLOW_COMMIT=false
ALLOW_DEPENDENCY_INSTALL=false
MAX_MUTATION_TARGET_FILES=5
MUTATION_TARGET_INITIAL=60
MUTATION_TARGET_MATURE=75

OPTIONAL INPUTS:
- Existing TODO_test-coverage.md
- Existing coverage report

MISSION:
Clone or open the provided GitHub repository, detect mutation testing support, select bounded mutation targets, run mutation tests where feasible, classify surviving mutants, and implement targeted test hardening to improve test effectiveness.

PRIMARY OUTPUT:
Maintain a workflow ledger named:
TODO_mutation-testing.md

STRICT RULES:
- Accept the GitHub repository URL as the target input.
- Prefer consuming TODO_test-coverage.md if present.
- Do not invent mutation scores.
- Do not install mutation tools unless explicitly allowed.
- Do not weaken tests to make mutants pass/fail artificially.
- Do not modify production code unless ALLOW_PRODUCTION_FIXES=true.
- Do not commit unless ALLOW_COMMIT=true.
- Every surviving mutant classification must include evidence.
- Every actionable item must be a checkable Markdown task with a stable ID.

PHASES:
1. Validate input repository URL.
2. Clone/open repository and checkout branch if provided.
3. Capture commit, branch, status, and timestamp.
4. Read TODO_test-coverage.md or coverage reports if available.
5. Detect mutation testing tool from project evidence.
6. Select max 5 mutation targets by risk and coverage readiness.
7. Run scoped mutation testing.
8. Classify surviving mutants.
9. Implement targeted test hardening.
10. Run focused tests.
11. Re-run scoped mutation tests.
12. Document equivalent mutants.
13. Finalize TODO_mutation-testing.md.
14. If ALLOW_COMMIT=true and validation passes, create a commit.

SURVIVING MUTANT CLASSIFICATIONS:
- Missing assertion.
- Missing edge case.
- Missing error-path test.
- Over-mocked behavior.
- Untested branch.
- Equivalent mutant.
- Production ambiguity.

FINAL RESPONSE:
Summarize:
- Repository analyzed.
- Mutation tool detected.
- Files targeted.
- Mutation score before/after.
- Tests hardened.
- Remaining survivors.
- Commands passing/failing.
- Whether commit was created.
```
