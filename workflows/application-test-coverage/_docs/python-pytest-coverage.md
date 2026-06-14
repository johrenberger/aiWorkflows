# Python + pytest + coverage.py Reference

**Purpose:** Python-specific guidance for the application-test-coverage
workflow. The main `workflow.md` is language-agnostic; this doc
captures the patterns that worked (and the pitfalls) when running the
workflow against a Python 3.13 / pytest 8.4 / coverage 7.14 codebase.

## Stack detection

For a Python repo, the expected signals are:

| Signal | Where to look |
|---|---|
| `pyproject.toml` (PEP 621) | build system, dependencies, tool config |
| `setup.cfg` or `setup.py` | legacy, some projects still use this |
| `requirements*.txt` | dependency lists |
| `conftest.py` | pytest fixtures and config |
| `tests/` directory | test files |
| `src/<package>/` or `<package>/` | source layout (src-layout vs flat-layout) |
| `pytest.ini` or `[tool.pytest.ini_options]` in pyproject | pytest config |

Pre-flight checks:
- `python3 --version` → expect 3.10+ (3.13 is current)
- `python3 -m pytest --version` → pytest 8.x or 9.x
- `python3 -m coverage --version` → coverage 7.x
- `pytest-cov` plugin: `python3 -c "import pytest_cov"` (catches missing install)

## Coverage command

For a single-module Python project (no Maven-style multi-module
build), the standard invocation is:

```bash
python3 -m pytest tests/ --cov=src/<package> --cov-report=term --cov-report=json:/tmp/cov.json -q
```

Why `--cov=src/<package>` (not `--cov=<package>`): for src-layout
projects, the package is not importable from the repo root, so
`--cov=<package>` will give 0% coverage even if the tests work.
The src-layout is the modern recommendation (avoids accidental
imports of the working tree).

For multi-module Python projects (workspace with multiple pyproject.toml
files), see `_docs/multi-module-orchestration.md`. The src-layout
typically lives under each sub-package, so the `--cov` argument
becomes a list: `--cov=src/pkg1 --cov=src/pkg2 ...`.

## Branch coverage (optional, often not enabled)

The application-test-coverage workflow targets line coverage by default
(`COVERAGE_TARGET_PER_FILE=90%` line). Branch coverage is a stronger
signal but rarely enabled in Python pyproject.toml.

To enable branch coverage:

```toml
# pyproject.toml
[tool.coverage.run]
branch = true

[tool.coverage.report]
# (optional) fail_under = 90
```

When branch coverage is enabled, the per-file table in the ledger
should also report branch %. The default Phase 5 command becomes:

```bash
python3 -m pytest tests/ --cov=src/<package> --cov-branch --cov-report=term -q
```

## Mutation testing

Mutation testing is the strongest signal for test quality, but the
Python ecosystem's two main tools (mutmut, cosmic-ray) have gotchas
that have caused me to use a manual script instead.

### mutmut

```bash
mutmut run --paths-to-mutate=src/<package>/<file>.py
mutmut results
mutmut show <id>
```

**Gotcha:** mutmut copies the source into `mutants/src/<package>/`
and chdirs into `mutants/` for the test run. If your code imports
from a sibling module (very common in Python), and the sibling
module is NOT in your mutation target, the import fails because
`mutants/src/<package>/` only has the targeted file.

**Workaround:** manually copy the entire source into `mutants/`
before running, OR scope mutmut to a single file AND a single test
file that doesn't import other modules of the package. The latter
is rarely achievable in a real codebase.

### cosmic-ray

```bash
cosmic-ray init requirements.txt cr.db
cosmic-ray exec cr.db
cosmic-ray report cr.db
```

**Gotcha:** more robust than mutmut (handles cross-file imports),
but requires a `requirements.txt` or explicit module list. Slower
startup. Heavier footprint (PostgreSQL or JSON-backed store).

### Manual mutation script (recommended for small batches)

For a focused mutation pass on a single file, a manual script is
faster and more transparent than either tool. The pattern:

```python
# mutation-check.py
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent
SRC = REPO / "src" / "<package>"

MUTANTS = [
    # (filename, original, replacement, label, test_files)
    (
        "file.py",
        "if foo:",
        "if False:",  # mutation: never enter the if
        "GAP-XXX: foo branch always False",
        ["tests/test_target.py"],
    ),
    ...
]

def run_mutant_check():
    for relpath, original, mutated, label, tests in MUTANTS:
        path = SRC / relpath
        text = path.read_text()
        if original not in text:
            print(f"ERROR: original not found in {relpath}")
            continue
        backup = text
        path.write_text(text.replace(original, mutated, 1))
        try:
            r = subprocess.run(
                ["python3", "-m", "pytest", *tests, "-q", "--no-cov", "-p", "no:randomly"],
                cwd=REPO, capture_output=True, timeout=120
            )
            status = "KILLED" if r.returncode != 0 else "SURVIVED"
            print(f"[{status}] {label}")
        finally:
            path.write_text(backup)  # always restore

if __name__ == "__main__":
    run_mutant_check()
```

The script saves to the task workspace as a re-runnable artifact
(e.g. `tasks/<date>-<project>-<pass>/reports/mutation-check.py`).

### Surviving mutants are often legitimate

When a mutation "survives" (tests pass despite the mutation), the
mutation is observationally equivalent for the test inputs. Common
cases:
- **Order swap** (A-then-B vs B-then-A) when only one matches
- **Default-value change** (e.g. `count=0` vs `count=1`) when no
  test triggers the case where the default matters
- **Off-by-one** at a boundary no test crosses

The honest report is "X/Y killed; (Y-X) legitimate survivors" with
a note explaining what additional test would catch the survivors.
Do NOT chase surviving mutants with synthetic tests; that creates
over-specific tests that don't reflect real usage.

## Test design patterns that worked

### BDD-TDD docstring + function-name-as-assertion

```python
def test_analyze_runtime_emits_deprecation_warning(tmp_path: Path):
    """analyze_runtime() emits DeprecationWarning (it's the deprecated wrapper)."""
    # Given: a JSONL log file with 1 valid runtime metrics entry
    log = _write_log(tmp_path, [...])
    # When:  analyze_runtime is called
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        analyze_runtime([log])
    # Then:  a DeprecationWarning is emitted
    assert any(issubclass(warning.category, DeprecationWarning) for warning in w)
```

79 tests over 2 PRs used this pattern. Stayed self-documenting
through merges. Function name = the assertion, docstring = the
narrative. Cost: 4-6 lines per test; benefit: anyone can answer
"what does this test?" without reading the assertion.

### Constructor quirks are worth pinning

When you find that a Pydantic/dataclass model takes a specific
positional argument you didn't expect, write a tiny test that
constructs it. Example from SGP:
- `ScorecardEntry(artifact_name, decision, roi_score, rationale, ...)`
  has NO `artifact_path` (despite the name suggesting one)
- `ResponsibilityReport(artifact_name, responsibility_score, flag,
  rationale, responsibilities=[...])` — `rationale` is REQUIRED
- `count_blocking(result)` takes 1 arg, not 2 (the 2nd-arg waivers
  parameter was removed at some point)

These are "obvious once you see them" but cost an hour each the
first time. A 1-line test that constructs the model and asserts
the field exists saves that hour next time.

### Test data builders (the `_write_log` pattern)

When many tests need similar fixtures, write a small private helper
in the test file (not in `conftest.py`) that constructs the fixture.
This keeps the test file self-contained and makes the test's
"Given" section trivial.

## The BDD-TDD red-phase workflow

For each gap in the gap-backlog:

1. **Read the gap text** — the gap usually describes the contract
2. **Read the current code** — find the line(s) that would need to
   change to break the contract
3. **Write the test in the desired (passing) form** — `Given/When/Then`
   docstring + function-name-as-assertion
4. **Run the test** — confirm it FAILS for the right reason (red phase)
5. **If the test passes already, the gap was wrong** — the code
   already exhibits the desired behavior; remove the test or weaken it
6. **Make the minimal source change to make it pass** — smallest
   possible diff
7. **Run again** — confirm GREEN
8. **Add a mutation** to the source change and confirm the test
   kills it
9. **Move to next gap**

This is the BDD-TDD loop. Skipping step 4 (the red phase) is the
#1 cause of false-positive tests that pass vacuously.
