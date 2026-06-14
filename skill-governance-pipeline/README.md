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

## Pre-commit hook

SGP can install a git pre-commit hook into a target repo that
blocks commits when staged skill/agent files have blocking
governance findings.

### Install

```bash
# In the target repo (the one containing skills/ and/or agents/):
python3 -m skill_governance.cli install-hooks .

# Or from the SGP checkout, pointed at a different repo:
python3 -m skill_governance.cli install-hooks /path/to/your/skill-repo
```

This copies the hook script from the SGP package into
`<target-repo>/.git/hooks/pre-commit` and marks it executable.

### What the hook does

On every `git commit`:

1. Reads the staged file list via `git diff --cached --name-only`
2. Filters to files matching `**/SKILL.md` or `**/*AGENT.md`
3. If none match, exits 0 (no work to do — fast path)
4. Otherwise, runs `sgp validate-files` on the staged files
5. Exits non-zero if any blocking finding is present (commit blocked)
6. Exits 0 if all staged files pass

### Required config

The hook looks for a governance config in the target repo's root,
in this order:

1. `governance.yaml`
2. `governance.local.yaml`
3. `governance.default.yaml`

If none exists, the hook prints a warning and exits 0 (does not
block). To enforce SGP validation in the target repo, copy
`config/governance.default.yaml` from this repo to the target
repo's root as `governance.yaml` and customize as needed.

### Bypassing the hook

`git commit --no-verify` skips the hook. Use sparingly; usually
a sign the rule is too strict, not that the commit should be
bypassed.

### Running validation manually

You can also run the same check without installing the hook:

```bash
python3 -m skill_governance.cli validate-files \
    --config /path/to/governance.yaml \
    path/to/skill1/SKILL.md \
    path/to/agent1/AGENT.md
```

The command exits 0 (clean) or 2 (blocking findings) so it works
in any pre-commit-style workflow.

## recommend-task

The `recommend-task` subcommand takes a natural-language task
description and returns the top N agents + skills best suited
for the task. It's a "where do I start?" tool for users who
don't yet know the catalog.

### Example

```bash
python3 -m skill_governance.cli recommend-task \
    --config config/governance.yaml \
    --top-n 3 \
    "deploy my app to production"
```

Output:

```
recommend-task: top 3 match(es) for 'deploy my app to production'

  1. [agent] DEVOPS_AGENT (score=0.667)
  2. [agent] MONITORING_AGENT (score=0.333)
  3. [agent] PEN_TESTING_AGENT (score=0.333)
```

### How it works

The matcher is deterministic (no LLM) and inspectable:

1. **Tokenize** the task: lowercase, remove punctuation, remove
   stopwords, apply lightweight stemming (so "deploy" matches
   "deployment" and "deployed")
2. **Index** the catalog: each artifact's `purpose` and body
   situation text are tokenized into a per-artifact token set
3. **Score** each artifact by **overlap coefficient**:
   `|intersection| / min(|task_tokens|, |artifact_tokens|)`.
   This rewards any overlap regardless of artifact length.
4. **Sort** by score descending, return the top N (default 3)

### Pair with the catalog guide

The matcher is a fast first pass. For richer navigation, point
users at the [CATALOG.md](https://github.com/johrenberger/test-repo/blob/main/agents/CATALOG.md)
in the test-repo: a one-page decision guide that maps
"you need to..." situations to agents.

### Limitations

- The matcher is keyword-based; paraphrases that don't share
  vocabulary may not match (e.g. "ship a fix" might miss
  "deploy"). Pair with the catalog guide for nuanced cases.
- Templates and references in the catalog (artifact_type
  `unknown`) are still indexed. They sometimes beat agents
  in the ranking because their titles are keyword-dense.
  This is a separate SGP improvement (filter `unknown` from
  the catalog) and not a matcher bug.

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
