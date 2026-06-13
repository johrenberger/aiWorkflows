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
