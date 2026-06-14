# Skill Governance Pipeline

Production-grade governance pipeline for the OpenClaw / MiniMax
environment. Audits existing skills and agents, enforces quality
gates, identifies inefficiencies, detects overlap, and generates
proposed rewritten versions of weak or redundant skills.

## What it does

1. **Discovers** every skill and agent in a directory tree
2. **Validates** metadata and contracts (CI-blocking on failure)
3. **Analyzes** dependencies, responsibility boundaries, semantic overlap
4. **Estimates** static and runtime token cost
5. **Scores** ROI per skill
6. **Runs benchmarks** against fixtures
7. **Recommends** keep / rewrite / merge / split / deprecate / retire
8. **Generates** proposed rewrites for weak artifacts
9. **Blocks CI** on critical findings
10. **Reports** business-grade executive + technical outputs

## Install

```bash
cd skill-governance-pipeline
pip install -e ".[test]"
```

## Configuration

The default config is at `config/governance.default.yaml`. You can
override individual settings via a custom YAML file.

```bash
skill-governance full --config my-config.yaml
```

## Commands

| Command | What it does |
| --- | --- |
| `scan` | Discover all skills and agents |
| `validate` | Run metadata + contract + dependency validation |
| `benchmark` | Run benchmark fixtures |
| `recommend` | Generate recommendations (no rewrites) |
| `rewrite` | Generate proposed rewrites |
| `report` | Render executive + technical reports |
| `ci` | Run all checks, exit non-zero on critical findings |
| `full` | Scan → validate → benchmark → recommend → rewrite → report → ci |

```bash
# Full pipeline
skill-governance full --config config/governance.default.yaml

# CI mode
skill-governance ci --config config/governance.default.yaml

# Generate a proposed rewrite for a specific artifact
skill-governance rewrite --artifact repo-discovery
```

## Human-in-the-loop for rewrite proposals

The `rewrite` command **proposes**, it does not apply. The output
lives in `output/proposed_rewrites/{artifact_name}.rewrite.md` —
a structured proposal that a human reviews and either accepts
(manually replaces the original) or rejects.

This is deliberate. Auto-applying a rewrite would silently change
behavior in a system that governs behavior. The proposal is a
suggestion; the human decides.

### The workflow

1. **Run the pipeline.** `skill-governance full` produces
   `remediation_backlog.md` (the prioritized list) and
   `output/proposed_rewrites/*.rewrite.md` (the proposals).
2. **Read the backlog.** Each entry has a priority, the affected
   artifact, the rationale (blockers + warnings), and the
   next action (`Open a rewrite task for X`).
3. **Open a rewrite task per proposal.** One task per
   recommendation, not one task for the whole batch. Each
   proposal is independent; batching risks merging unrelated
   changes.
4. **Read the proposal file.** It is a complete replacement
   candidate with YAML frontmatter, a "Why this rewrite was
   triggered" section, a "What changed" summary, the
   token-efficiency budget, and a migration checklist.
5. **Decide:** accept (manually replace the original with the
   proposal), refine (edit the proposal first, then apply), or
   reject (file a waiver instead, or just close the task).
6. **Re-run `validate`.** Confirm the new artifact passes
   `skill-governance validate` with no blocking findings. The
   rewrite was supposed to fix the blockers; if it didn't, the
   proposal is wrong.

### Anatomy of a proposal file

A `.rewrite.md` file is a complete replacement candidate. The
structure is:

- **YAML frontmatter** — `name`, `artifact_type`, `purpose`,
  `category`, `owner`, `version`, `inputs`, `outputs`,
  `dependencies`, `intended_consumers`, `quality_level`,
  `last_reviewed`. Every field is required; missing fields
  are part of why the rewrite was triggered.
- **Why this rewrite was triggered** — the categories of
  finding that drove the recommendation (e.g. `roi-decision-rewrite`,
  `vague-output`, `circular-dependency`).
- **What changed** — a numbered list of structural fixes
  (metadata completeness, input/output contract, boundaries,
  validation expectations).
- **Token efficiency** — the original estimated tokens and
  the target. Single-purpose skills should stay under 2,000
  tokens; if the target is higher, the skill is over-broad.
- **Validation expectations** — the pass criteria for
  `skill-governance validate` after the rewrite is applied.
- **Original excerpt** — the relevant lines of the original
  artifact, for context.
- **Compatibility and migration** — what the rewrite preserves,
  what it tightens, and a 3-step migration procedure.

### Worked example

Say the `validate` step finds a `repo-discovery` skill with
`vague-output` findings and `quality_level: draft`. The
`recommend` step decides `rewrite` (not `merge`, not
`deprecate`). The `remediation_backlog.md` shows:

```
## rec-4bcea911 — rewrite (priority 2)

- **Affected:** repo-discovery
- **Rationale:** 1 blocking + 2 warnings on repo-discovery.
- **Effort:** M
- **Risk:** low
- **CI impact:** blocking
- **Next action:** Open a rewrite task for repo-discovery.
```

You then:

1. Open a task: "Apply rewrite proposal for `repo-discovery`".
2. Read `output/proposed_rewrites/repo-discovery.rewrite.md`.
3. Notice the proposal adds a strict YAML frontmatter and
   tightens the `purpose` field to 1-2 sentences. The
   `intended_consumers` field goes from `[]` to a list of
   specific consumers.
4. The proposal's "Validation expectations" section says
   `skill-governance validate` should now show 0 blocking
   findings for `repo-discovery`.
5. Apply the proposal by replacing
   `path/to/repo-discovery/SKILL.md` with the content of
   `output/proposed_rewrites/repo-discovery.rewrite.md`
   (minus the "Why this rewrite was triggered" comment
   block — that's not part of the artifact).
6. Re-run `skill-governance validate` and confirm 0
   blocking findings on `repo-discovery`. The rewrite task
   is done; close it.

### Filtering to one proposal

If you only want the proposal for a single artifact
(useful for review or for testing a fix without re-running
the full pipeline):

```bash
skill-governance rewrite --config config/governance.default.yaml \
  --artifact repo-discovery
```

The full pipeline still runs, but only the matching
proposal is printed to the console. The proposal file is
still written to `output/proposed_rewrites/`.

## Outputs

All outputs land in `output/`:

| File | Purpose |
| --- | --- |
| `skill_inventory.json` | Discovered artifacts |
| `dependency_graph.json` | Cross-skill dependency graph |
| `token_cost_static.json` | Static token estimates |
| `runtime_token_metrics.json` | Runtime token metrics (if logs available) |
| `governance_findings.json` | All findings (CI-blocking + warnings) |
| `skill_scorecard.json` | Per-skill ROI / quality score |
| `executive_report.md` | One-page business summary |
| `technical_report.md` | Detailed technical findings |
| `remediation_backlog.md` | Prioritized fix list |
| `proposed_rewrites/` | Generated rewrite proposals |

## Governance operating model

- **Deterministic first**: file hashes, token counts, dependency
  detection, and contract parsing are all deterministic.
- **MiniMax only for judgment**: semantic overlap, responsibility
  coherence, and ROI scoring use MiniMax semantic scoring.
- **Token savings never override quality**: a rewrite that
  reduces tokens but drops benchmark score below threshold is
  rejected.
- **CI blocks by default**: missing metadata, missing contracts,
  missing dependencies, circular deps, benchmark failures, and
  critical low ROI are all CI blockers.
- **Waivers are explicit**: a finding can be waived only with
  an owner, rationale, and expiration date.

## Development

```bash
# Run tests
pytest

# Run a single test
pytest tests/test_discovery.py -v

# Run with coverage
pytest --cov=skill_governance
```

## License

MIT
