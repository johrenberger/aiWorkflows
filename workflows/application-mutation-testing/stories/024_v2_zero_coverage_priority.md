# Story 024 — v2: surface zero-coverage files as a separate `zero_coverage_queue` artifact and `--zero-coverage-only` flag

## Why

Story 022 surfaced a real Broadleaf-shaped problem: out of 947
`risk_scores.json` records for `broadleaf-common`, **653 source files
have `line_coverage=0.0`** — i.e. they were never exercised by any
test. Another 294 have some coverage, ranging from 0.01% to 100%.

Today, `test-factory queue` produces a single `test_gap_queue.json`
sorted by `priority = risk_score * coverage_gap`. Zero-coverage files
are mixed in with low-coverage files based on their risk_score. A user
who wants to answer "what's still completely untested in this repo?"
has to filter the 947-item list by `line_coverage == 0.0` themselves.

This story makes that answer a one-flag CLI invocation and a
first-class artifact.

## What's in this PR

1. **`queue()` annotates every item with `zero_coverage: bool`** —
   `True` when `line_coverage == 0.0` AND
   `branch_coverage in (None, 0.0)`. This means a file with no test
   coverage at all (the 653 files) and a file whose tests ran but
   hit zero lines are both flagged. The annotation is added to
   `test_gap_queue.json` items in-place; downstream consumers don't
   need to filter.

2. **New artifact `zero_coverage_queue.json`** — same items as
   `test_gap_queue.json` but filtered to `zero_coverage == True`,
   sorted by `risk_score` descending (then by `path` for
   determinism). The reasoning: once we know the file has zero
   coverage, `priority = risk_score * coverage_gap` collapses to
   `risk_score * 180` for all of them (since `coverage_gap` is
   always at its max for zero-coverage items), so sorting by
   `risk_score` is the meaningful axis.

3. **New CLI flag `--zero-coverage-only`** on filter-style subcommands
   (`queue`, `workitems`, `report`, `run`) — when set, the
   subcommand's output is filtered to only zero-coverage items
   (using the same `zero_coverage` flag). On `run`, this affects
   only the `queue` and `workitems` outputs; `report` filters the
   queue section it embeds. (The flag is rejected on `branch`,
   `commit`, `coverage`, `score`, `scan` — those don't have a queue.)

4. **Updated `final_report.md`** — adds a "Zero-Coverage Files"
   section that shows the count and the top 10 zero-coverage items
   by `risk_score`, so the report tells the user "you have N
   completely untested files; here are the riskiest ones" without
   requiring the user to run a second command.

## Acceptance scenarios

### Scenario 1: `queue` annotates every item with `zero_coverage`

**Given** a `risk_scores.json` with three records (line_coverage = 0.0,
30.0, 95.0) for paths `a.java`, `b.java`, `c.java` respectively
**When** `test-factory queue` runs
**Then** `test_gap_queue.json` contains all three records
**And** `a.java` has `zero_coverage: true`
**And** `b.java` has `zero_coverage: false`
**And** `c.java` has `zero_coverage: false`

### Scenario 2: `zero_coverage_queue.json` contains only zero-coverage items sorted by `risk_score` desc

**Given** the same three records from Scenario 1 plus an extra
zero-coverage record with `risk_score=900.0` (the highest)
**When** `test-factory queue` runs
**Then** `zero_coverage_queue.json` exists
**And** it contains exactly 2 records (the two zero-coverage items)
**And** the highest-risk-score record appears first
**And** the second record is sorted by `path` (deterministic tiebreak)

### Scenario 3: `queue --zero-coverage-only` filters stdout output

**Given** the same `risk_scores.json`
**When** `test-factory queue --zero-coverage-only` runs
**Then** stdout contains only the zero-coverage records
**And** exit code is 0
**And** `test_gap_queue.json` is unchanged (still contains all items)

### Scenario 4: `final_report.md` shows the zero-coverage section

**Given** the same `risk_scores.json`
**When** `test-factory report` runs
**Then** `final_report.md` contains a "Zero-Coverage Files" section
**And** the section header shows the count
**And** the section lists the top 10 zero-coverage items by `risk_score`

### Scenario 5: `run --zero-coverage-only` filters workitems output

**Given** the same `risk_scores.json` plus a corresponding
`repo_inventory.json` so `workitems()` can run
**When** `test-factory run --zero-coverage-only` runs
**Then** `workitems.json` (or whatever the artifact is) contains only
zero-coverage items
**And** `zero_coverage_queue.json` is written

## Scope limits (deliberate)

- **No change to `priority` formula.** The existing
  `priority = risk_score * coverage_gap` already works correctly;
  zero-coverage items get a high `coverage_gap` (180) so they
  naturally float to the top of `test_gap_queue.json` when their
  `risk_score` is also high. The new flag is purely a *visibility*
  improvement.
- **No change to which files are considered "zero coverage."** We
  follow the same definition v2 already uses: `line_coverage == 0.0`
  AND `branch_coverage in (None, 0.0)`. This is a slight
  generalization of "completely untested" — files whose tests
  executed but hit no lines also count.
- **No default change.** The `zero_coverage_queue.json` artifact
  is *additive* — it gets written whenever `queue()` runs. The
  `--zero-coverage-only` flag is opt-in.
- **`--zero-coverage-only` on `report` filters the queue section
  only.** Coverage baseline, risk-weighted index, and the other
  report sections are not affected. Same for `run`.

## Out of scope

- Auto-surfacing zero-coverage files in `pr_summary.md` (the
  per-PR summary). That would change the meaning of an existing
  report; better as a separate follow-up if users want it.
- Pushing zero-coverage work items into a separate tracker
  (e.g. Jira/Linear). Out of scope — v2's job ends at writing
  the artifact and the CLI output.

## End-to-end evidence

On a real Broadleaf run (`/tmp/v2-broadleaf-full/`):
- 947 total `risk_scores.json` records
- 653 with `line_coverage == 0.0`
- After this change: `zero_coverage_queue.json` will contain 653 items
  sorted by `risk_score` desc
- `test-factory queue --zero-coverage-only --module common` will
  return 653 records (the cross-module view is unchanged from story 023)
- `final_report.md` will have a new section showing the 653 count and
  the top 10 by `risk_score`

## Tests

- 6 new BDD tests in `tests/test_024_v2_zero_coverage_priority.py`
- Tests verify: annotation on each item, separate artifact contents
  and sort order, `--zero-coverage-only` filtering for `queue` and
  `run`, and the new `final_report.md` section.
- v2 target: 92 + 6 = 98 pass (current 92 includes story 023's 7).
- Mutation: 132/133 (1 pre-existing skip, unchanged).
