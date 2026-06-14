# Changelog

All notable changes to `skill-governance-pipeline` (SGP) are
documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-06-14

The first stable release of the Skill Governance Pipeline. SGP
is a production-grade governance pipeline for OpenClaw skills
and agents: it discovers, validates, scores, recommends, and
emits rewrites for artifacts in a skill/agent catalog.

### Added

- **Discovery** (`discovery.py`): recursive scan with content-hash
  dedup. Single-pass, no LLM.
- **Metadata parser** (`metadata_parser.py`): YAML frontmatter +
  JSON metadata, robust to missing fields.
- **Contract validator** (`contract_validator.py`): vague-output
  detection (TBD, lorem-ipsum, etc.).
- **Dependency analyzer** (`dependency_analyzer.py`): DFS cycle
  detection, missing/unused dep detection.
- **Responsibility analyzer** (`responsibility_analyzer.py`):
  verb-counting heuristic with frontmatter stripping.
- **Overlap analyzer** (`overlap_analyzer.py`): Jaccard + bag +
  name blend. Configurable thresholds.
- **Token analyzer** (`token_analyzer.py`): 4-chars-per-token
  static estimation.
- **ROI scorer** (`roi_scorer.py`): 8-factor weighted formula
  with merge/split/deprecate/keep decisions.
- **Benchmark runner** (`benchmark_runner.py`): YAML fixtures
  with weighted rules.
- **Rewrite generator** (`rewrite_generator.py`): 10-section
  rewrite proposals (HITL-applied).
- **Recommendation engine** (`recommendation_engine.py`):
  per-artifact + merge + split recommendations, sorted by priority.
- **Report generator** (`report_generator.py`): executive +
  technical + remediation backlog.
- **CI gate** (`ci_gate.py`): waiver-aware blocking evaluation.
- **Waiver store** (`waiver_store.py`): YAML waivers, expiration-aware.
- **History** (`history.py`): JSONL run history, trend analysis.
- **Config loader** (`config_loader.py`): YAML config with attr+dict access.
- **Cross-references** (`cross_references.py`): bidirectional
  consistency checks for `uses_skills` / `used_by_agents`.
- **Recommendation task** (`recommend_task.py`): natural-language
  task → ranked agent+skill recommendations. Overlap-coefficient
  scoring, lightweight stemmer.
- **Runtime metrics** (`runtime_metrics.py`): real JSONL parser
  (Phase 7 fix from stub).
- **CLI** (`cli.py`): 9 Click commands (`scan`, `validate`,
  `benchmark`, `recommend`, `rewrite`, `report`, `ci`, `full`,
  `validate-files`, `install-hooks`, `recommend-task`).
- **Pre-commit hook** (`hooks/pre-commit`): bash script that
  validates staged `*AGENT.md` and `SKILL.md` files.
- **Configuration templates**: `config/governance.default.yaml`,
  `config/waivers.yaml`.

### Quality metrics

- **Tests:** 407 (was 75 at v0.1.0 baseline; 5.4x increase)
- **Branch coverage:** 94.0%
- **Modules at ≥90%:** 23 of 23 (100%)
- **mypy:** 0 issues (permissive strict mode)
- **ruff:** 0 issues
- **Gap-backlog:** 14 of 14 closed
- **Mutation score on most-asserted files:** 52%
  (post-#49 hypothesis property tests; was 0% at baseline)

### Performance

- **Real catalog (121 artifacts):** end-to-end pipeline runs
  in <30 seconds
- **Pre-commit hook:** <5s for fast-path exit (no relevant
  files staged); ~30s for full validation

### Documentation

- **README.md** (442 lines): what it does, install,
  configuration, 9 commands, HITL workflow, pre-commit hook,
  `recommend-task`, governance operating model, development
- **TODO_test-coverage.md** (251 lines): per-file coverage
  ledger with v3 baseline
- **CHANGELOG.md** (this file)

### Lessons captured

110 lessons across the development arc, including:

- **Lesson #59**: Health-score formulas: "100 minus penalty" clamps
  to 0; use per-artifact clean/ugly/broken → 100/80/30 weighted.
- **Lesson #70**: Line coverage (84%) and mutation score (~0%)
  can disagree by an order of magnitude. The 5 hardening tests
  pushed mutation score from 0% to 52% on the targeted files.
- **Lesson #97**: DDT for enumerable input spaces, Hypothesis
  for unbounded ones.
- **Lesson #107**: Overlap coefficient > Jaccard for asymmetric
  sets (task vs artifact length).
- **Lesson #111**: Filter at the right layer (CLI decides
  what to recommend; the matcher matches what you give it).

### Open follow-ups (not in 1.0.0)

- DDT rewrite of property-based tests (per lesson #97)
- Tighten mypy strict mode (one switch at a time)
- Add type annotations to all 21 source files
- Run mutmut to re-measure mutation score post-property-tests
- Re-measure mutation score on all 21 modules (currently 3)

[1.0.0]: https://github.com/johrenberger/aiWorkflows/releases/tag/skill-governance-pipeline-v1.0.0
