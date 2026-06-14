"""
Acceptance tests for SGP Phase 6 (BDD-TDD).

Each scenario below is a black-box test of one of the 4 fixes
recommended after the v1.0.0 ship. They are intentionally written
BEFORE the implementation, so they will fail in the expected ways
on v1.0.0 and will pass once Phase 6 is complete.

Conventions:
- Docstring = Given/When/Then narrative
- Test function name = the assertion in plain English
- All tests use the real CLI (subprocess) against a fixture catalog,
  mirroring test_cli.py in v1.0.0
- Self-test at the bottom confirms the test file itself is wired in
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

PIPELINE_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = PIPELINE_ROOT / "tests" / "fixtures"
PIPELINE_SRC = PIPELINE_ROOT / "src"


# ---------------------------------------------------------------------------
# Test fixture: a minimal catalog that exercises all 4 fixes.
# - 1 well-written skill (with linter) — should score > 50
# - 1 README.md that gets discovered as "unknown" — should NOT be
#   contract-validated
# - 1 skill with cosmetic metadata gaps but otherwise valid — should
#   not drive the catalog health to 0
# ---------------------------------------------------------------------------
def _make_p6_catalog(tmp_path: Path) -> tuple[Path, dict]:
    """Create a small catalog + config that exercises Phase 6 acceptance criteria.

    Layout (matches the v1.0.0 test_cli.py convention):
        <tmp_path>/                 <-- config lives here
            config.yaml
            skills/                 <-- skill_directories points here
                good-skill/SKILL.md
                cosmetically-incomplete-skill/SKILL.md
                README.md
    The CLI resolves `artifact.path` against `config_path.parent.parent`,
    so the skill_directories must be a sibling of the config's parent.
    """
    # Skill 1: well-written, with linter and proper YAML frontmatter
    # (so contract validation passes; only metadata findings remain)
    s1 = tmp_path / "good-skill"
    s1.mkdir()
    (s1 / "SKILL.md").write_text(
        """---
name: good-skill
artifact_type: skill
purpose: >
  A well-written skill that passes contract validation and
  has full metadata. Used to anchor the health-score test.
category: validation
owner: engineering
version: 1.0.0
inputs:
  - name: artifact_path
    type: string
outputs:
  - name: lint_report
    type: json
dependencies: []
intended_consumers:
  - CI pipeline
quality_level: validated
last_reviewed: 2026-06-14
---

# Good Skill

## When to use

Trigger on inbound tasks that need this skill.

## When NOT to use

Do not use for unrelated work.

## Workflow

1. Do the thing.
2. Verify the thing.

## Validation

Run `python3 scripts/lint-good.py --self-test`.
"""
    )
    scripts_dir = s1 / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "lint-good.py").write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        "if len(sys.argv) > 1 and sys.argv[1] == '--self-test':\n"
        "    print('PASS')\n"
        "    sys.exit(0)\n"
        "sys.exit(0)\n"
    )

    # Skill 2: missing some metadata fields but otherwise valid
    # (purpose present, contracts structured → contract validation passes;
    # only metadata-missing findings remain → all cosmetic)
    s2 = tmp_path / "cosmetically-incomplete-skill"
    s2.mkdir()
    (s2 / "SKILL.md").write_text(
        """---
name: cosmetically-incomplete-skill
artifact_type: skill
purpose: >
  A skill that has structured contracts but is missing several
  cosmetic metadata fields. Used to test the health-score formula.
inputs:
  - name: file_path
    type: string
outputs:
  - name: result_json
    type: json
dependencies: []
---

# Cosmetically Incomplete Skill

## When to use

Trigger on X.

## When NOT to use

Do not use for Y.

## Workflow

1. Step one.
2. Step two.
"""
    )

    # README that will be discovered as 'unknown'
    (tmp_path / "README.md").write_text(
        "# Skills Directory\n\nThis directory contains skills.\n"
    )

    # Config
    config = {
        "skill_directories": [str(tmp_path)],
        "agent_directories": [],
        "output_directory": str(tmp_path / "output"),
        "token_thresholds": {"high_cost": 8000},
        "overlap_thresholds": {"blocking": 85, "warning": 70},
        "roi_thresholds": {"keep_min": 70, "rewrite_min": 50, "deprecate_max": 30},
        "benchmark_thresholds": {"default_minimum": 0.7},
        "ci_blocking_rules": [],
        "minimax_semantic_scoring_enabled": False,
        "waiver_file": str(tmp_path / "waivers.yaml"),
        "runtime_log_paths": [],
    }
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(yaml.dump(config))
    return cfg_path, config


def _run_cli(args: list[str], cwd: Path = PIPELINE_ROOT) -> subprocess.CompletedProcess:
    """Run the SGP CLI as a subprocess and return the result."""
    return subprocess.run(
        [sys.executable, "-m", "skill_governance.cli", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": str(PIPELINE_SRC), "PATH": "/usr/bin:/usr/local/bin"},
    )


# ===========================================================================
# Scenario #1a: `benchmark` subcommand runs end-to-end
# Given: a configured catalog with at least one benchmark fixture
# When: the user runs `python -m skill_governance benchmark --config …`
# Then: the command exits 0 and writes output/skill_scorecard.json
#   populated with benchmark results
# ===========================================================================
def test_benchmark_subcommand_runs_end_to_end_and_writes_scorecard(tmp_path):
    cfg, _ = _make_p6_catalog(tmp_path)
    result = _run_cli(["benchmark", "--config", str(cfg)])
    scorecard = tmp_path / "output" / "skill_scorecard.json"
    assert result.returncode == 0, (
        f"benchmark subcommand should exit 0, got {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert scorecard.exists(), (
        f"benchmark should write skill_scorecard.json (exists={scorecard.exists()})"
    )
    data = json.loads(scorecard.read_text())
    # Scorecard is a list of scorecard entries; must be non-empty for a non-empty catalog
    assert isinstance(data, list), f"skill_scorecard.json must be a JSON list, got {type(data)}"
    assert len(data) >= 1, f"scorecard must have at least one entry, got {len(data)}"


# ===========================================================================
# Scenario #1b: `recommend` subcommand runs end-to-end
# Given: a configured catalog
# When: the user runs `python -m skill_governance recommend --config …`
# Then: the command exits 0 and writes output/skill_scorecard.json
#   containing recommendation decisions
# ===========================================================================
def test_recommend_subcommand_runs_end_to_end_and_writes_scorecard(tmp_path):
    cfg, _ = _make_p6_catalog(tmp_path)
    result = _run_cli(["recommend", "--config", str(cfg)])
    scorecard = tmp_path / "output" / "skill_scorecard.json"
    assert result.returncode == 0, (
        f"recommend subcommand should exit 0, got {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert scorecard.exists(), (
        f"recommend should write skill_scorecard.json (exists={scorecard.exists()})"
    )


# ===========================================================================
# Scenario #1c: `rewrite` subcommand runs end-to-end
# Given: a configured catalog
# When: the user runs `python -m skill_governance rewrite --config …`
# Then: the command exits 0 and the run is not a stub
# ===========================================================================
def test_rewrite_subcommand_runs_end_to_end_not_a_stub(tmp_path):
    cfg, _ = _make_p6_catalog(tmp_path)
    result = _run_cli(["rewrite", "--config", str(cfg)])
    assert result.returncode == 0, (
        f"rewrite subcommand should exit 0, got {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "not yet implemented" not in result.stdout, (
        f"rewrite subcommand should not be a stub. stdout: {result.stdout}"
    )


# ===========================================================================
# Scenario #2: Health score distinguishes cosmetic vs structural
# Given: a catalog where every finding is in a cosmetic category
#   (metadata / discovery / contract)
# When: the pipeline runs `ci` end-to-end (which writes the report)
# Then: the catalog health score is > 0 (the new formula caps
#   cosmetic findings, where the old formula would give 0)
# ===========================================================================
def test_health_score_is_above_0_when_only_cosmetic_findings_present(tmp_path):
    cfg, _ = _make_p6_catalog(tmp_path)
    # Run `ci` — it goes through the full pipeline and writes the
    # executive report. (Don't use `full` because it calls `validate`
    # which sys.exit(2)s on blocking findings, killing the chain
    # before reports get written.)
    _run_cli(["ci", "--config", str(cfg)])
    exec_report = tmp_path / "output" / "executive_report.md"
    if not exec_report.exists():
        _run_cli(["report", "--config", str(cfg)])
    assert exec_report.exists(), (
        f"executive_report.md must be written. Got:\n"
        + (exec_report.read_text() if exec_report.exists() else "<missing>")[:800]
    )
    text = exec_report.read_text()
    m = re.search(r"\*\*Health score:\*\*\s*(\d+)/100", text)
    assert m, f"Health score line missing from executive report. Got:\n{text[:800]}"
    score = int(m.group(1))
    # Acceptance: the new health formula must give a non-zero score
    # for a catalog whose findings are entirely cosmetic (metadata /
    # discovery / contract). The OLD formula (100 - 5*blocking)
    # would give 0 here because there are > 20 blocking cosmetic
    # findings from the minimal catalog. The NEW formula caps
    # cosmetic findings and weights structural findings more
    # heavily, so a cosmetic-only catalog scores > 0.
    assert score > 0, (
        f"Catalog with only cosmetic findings must score > 0 (new formula caps "
        f"cosmetic weight). Got: {score}/100. Old formula would also give 0; "
        f"the new formula must distinguish."
    )


# ===========================================================================
# Scenario #3: Unknown artifacts are excluded from contract validation
# Given: a catalog with 1 skills/README.md that gets discovered as
#   artifact_type=unknown
# When: the pipeline runs `validate`
# Then: README.md produces zero blocking contract findings
# ===========================================================================
def test_unknown_artifact_excluded_from_contract_validation(tmp_path):
    cfg, _ = _make_p6_catalog(tmp_path)
    _run_cli(["validate", "--config", str(cfg)])
    findings_path = tmp_path / "output" / "governance_findings.json"
    assert findings_path.exists(), "validate must write governance_findings.json"
    findings = json.loads(findings_path.read_text())
    readme_findings = [
        f for f in findings
        if "README" in f.get("artifact_name", "") or "README" in f.get("artifact_path", "")
    ]
    blocking_on_readme = [f for f in readme_findings if f.get("severity") == "blocking"]
    assert len(blocking_on_readme) == 0, (
        f"README.md (unknown type) must NOT produce blocking contract findings. "
        f"Got {len(blocking_on_readme)} blocking findings:\n"
        + "\n".join(f"  - {f.get('message')}" for f in blocking_on_readme)
    )


# ===========================================================================
# Scenario #4: Every finding carries a stable artifact identifier
# Given: a catalog with multiple skills
# When: the pipeline runs `validate`
# Then: every finding has an `artifact_path` (or `artifact_id`) field
#   that groups findings by source artifact
# ===========================================================================
def test_every_finding_has_stable_artifact_identifier(tmp_path):
    cfg, _ = _make_p6_catalog(tmp_path)
    _run_cli(["validate", "--config", str(cfg)])
    findings_path = tmp_path / "output" / "governance_findings.json"
    assert findings_path.exists()
    findings = json.loads(findings_path.read_text())
    missing = [f for f in findings if "artifact_path" not in f and "artifact_id" not in f]
    assert len(missing) == 0, (
        f"Every finding must carry 'artifact_path' or 'artifact_id'. "
        f"{len(missing)}/{len(findings)} findings lack it."
    )


# ===========================================================================
# Self-test: confirm the test file itself is wired into pytest
# ===========================================================================
def test_acceptance_test_file_is_collectable():
    """Sanity check: this test file is picked up by pytest."""
    assert __file__.endswith("test_p6_acceptance.py"), (
        f"Test file naming must be test_*.py to be auto-collected, got {__file__}"
    )
