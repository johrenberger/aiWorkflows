# Phase 2 report — Skill Governance Pipeline

> Generated 2026-06-13T22:18:00Z by the `software-engineer` agent

## Phase 2 scope (per source spec)

- `dependency_analyzer` (CR 4) — graph, cycles, missing, unused
- `responsibility_analyzer` (CR 5) — deterministic heuristic
- `overlap_analyzer` deterministic layer (CR 6 — semantic in Phase 3)
- Expanded `report_generator` technical report
- Full `ci_gate` integration with config-driven rules

## Implementation

| Module | File | Lines (delta) | Status |
|---|---|---|---|
| dependency_analyzer | `src/skill_governance/dependency_analyzer.py` | 275 (new) | ✅ |
| responsibility_analyzer | `src/skill_governance/responsibility_analyzer.py` | 194 (new) | ✅ |
| overlap_analyzer | `src/skill_governance/overlap_analyzer.py` | 156 (new) | ✅ |
| report_generator | `src/skill_governance/report_generator.py` | 218 (+37) | ✅ expanded |
| cli | `src/skill_governance/cli.py` | 255 (+9) | ✅ wired in |
| Tests | `tests/test_dependency_analyzer.py`, `test_responsibility_analyzer.py`, `test_overlap_analyzer.py` | 288 (new) | ✅ |
| **Total (Phase 2 delta)** | | **+960** | **✅** |

## Tests

**38/38 unit tests pass** (was 25 in Phase 1; +13 from Phase 2).

| Test file | Tests | Pass |
|---|---|---|
| `test_discovery.py` | 6 | 6 |
| `test_metadata_parser.py` | 5 | 5 |
| `test_contract_validator.py` | 6 | 6 |
| `test_ci_gate.py` | 4 | 4 |
| `test_cli.py` | 4 | 4 |
| **`test_dependency_analyzer.py`** | **5** | **5** |
| **`test_responsibility_analyzer.py`** | **4** | **4** |
| **`test_overlap_analyzer.py`** | **4** | **4** |

## End-to-end validation

Ran `skill-governance ci --config config/governance.real.yaml`
against the real catalog (test-repo + aiWorkflows):

```
Inventory: 126 artifacts (was 129 in Phase 1; 3 dupes collapsed)
  - 96 skills
  - 21 agents
  - 9 unknown
Dependency graph: 56 nodes
  - 0 missing
  - 4 circular
  - 0 unused
Responsibility: 22 over-broad, 107 unclear, 0 coherent, 0 too-narrow
Overlap: 91 pairs scored
  - 1 merge candidate (>=85)
  - 0 differentiate (70-84)
  - 90 keep_separate (<70)
Blocking findings: 133 (was 132 in Phase 1; +1 from new dep circular)
Warnings: 2
Health score: 0/100
CI status: FAIL (expected; real skills lack metadata)
```

Reports generated:
- `output/dependency_graph.json` (NEW, ~10 KB)
- `output/technical_report.md` (35 KB, expanded)
- All previous reports still produced

## Decisions made

- **`D1`**: Use deterministic Jaccard + bag + name overlap (60/30/10
  blend) for overlap scoring. Semantic layer in Phase 3.
- **`D2`**: Use DFS for cycle detection (simple, sufficient for
  small graphs; Tarjan's SCC is overkill for typical skill counts).
- **`D3`**: Dedup discovered artifacts by content hash (not just
  path). This collapses shared templates/refs that appear in
  multiple skill subdirs.
- **`D4`**: Body-only action extraction (strip frontmatter) for
  responsibility scoring, so metadata tokens don't pollute the
  count.
- **`D5`**: Severity of "missing dep" and "circular dep" = BLOCKING;
  "unused dep" = WARNING. Matches the source spec's CI blocking
  rules.

## Handoff to Phase 3

The next segment should:
1. Implement `roi_scorer` (CR 8) with a real weighted formula
   combining reuse, token cost, output quality, dependency value,
   failure rate, semantic uniqueness, benchmark pass rate
2. Add MiniMax semantic scoring interface (mocked; real in Phase 5)
3. Implement `recommendation_engine` (CR 11) — rule-based
   recommendations from findings
4. Wire recommendations into reports and CI status
5. Add 4+ unit tests per new module

## Provenance

- Project: `skill-governance-pipeline/`
- Task: `2026-06-13-sgp-p2` (continuation of 2026-06-13-sgp)
- Started: 2026-06-13T22:12:00Z
- Phase 2 finished: 2026-06-13T22:18:00Z
- Wall time: ~6 minutes
- Total project wall time: ~17 minutes (Phase 1 + Phase 2)
