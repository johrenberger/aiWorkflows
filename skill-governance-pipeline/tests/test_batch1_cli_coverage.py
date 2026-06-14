"""BDD-TDD coverage tests for cli.py (Batch 1).

Triggered by application-test-coverage assessment: cli.py was 89%
(line coverage) and 85% (branch coverage). 27 statements uncovered
are mostly the 8 CLI subcommand bodies (benchmark, recommend,
rewrite, full) and the `_compute_health` empty-catalog branch.

Method: BDD-TDD
- Given/When/Then in docstring, function name = assertion
- Use Click's CliRunner for end-to-end CLI invocation
- Each test covers a specific missing-line block
"""
from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from skill_governance.cli import _compute_health, main
from skill_governance.models import (
    ArtifactType,
    PipelineResult,
    SkillArtifact,
)


def _artifact(name: str) -> SkillArtifact:
    return SkillArtifact(
        name=name,
        path=name + ".md",
        artifact_type=ArtifactType.SKILL,
        size_bytes=100,
        estimated_tokens=25,
        content_hash="x" * 64,
        modified_timestamp="2026-06-13T00:00:00Z",
        body_excerpt="test",
    )


# ===========================================================================
# SCENARIO 1: `full` CLI command runs the full pipeline
#
# Given: a valid config and tmp output dir
# When:  `sgp full --config <path>` is invoked via CliRunner
# Then:  exit code is 0 and the message indicates scan/validate/etc ran
# ===========================================================================
def test_full_command_runs_complete_pipeline(tmp_path: Path):
    """The `full` CLI command runs scan -> validate -> ... -> ci."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "skill_directories: []\n"
        "agent_directories: []\n"
        "output_directory: " + str(tmp_path / "out") + "\n"
        "token_thresholds: {high_cost: 8000}\n"
        "overlap_thresholds: {blocking: 60, warning: 40}\n"
        "roi_thresholds: {keep_min: 70, rewrite_min: 50, deprecate_max: 30}\n"
        "benchmark_thresholds: {default_minimum: 0.7}\n"
        "ci_blocking_rules: []\n"
        "minimax_semantic_scoring_enabled: false\n"
        "waiver_file: " + str(tmp_path / "waivers.yaml") + "\n"
        "runtime_log_paths: []\n"
    )
    (tmp_path / "waivers.yaml").write_text("waivers: []\n")
    runner = CliRunner()
    result = runner.invoke(main, ["full", "--config", str(cfg)])
    assert result.exit_code == 0, f"expected exit 0, got {result.exit_code}: {result.output}"


# ===========================================================================
# SCENARIO 2: `benchmark` CLI command writes skill_scorecard.json
#
# Given: a valid config
# When:  `sgp benchmark --config <path>` is invoked
# Then:  the scorecard JSON file is written, with a "benchmark: ran N
#        benchmarks" message printed
# ===========================================================================
def test_benchmark_command_writes_scorecard(tmp_path: Path):
    """The `benchmark` CLI command writes skill_scorecard.json and prints message."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "skill_directories: []\n"
        "agent_directories: []\n"
        "output_directory: " + str(tmp_path / "out") + "\n"
        "token_thresholds: {high_cost: 8000}\n"
        "overlap_thresholds: {blocking: 60, warning: 40}\n"
        "roi_thresholds: {keep_min: 70, rewrite_min: 50, deprecate_max: 30}\n"
        "benchmark_thresholds: {default_minimum: 0.7}\n"
        "ci_blocking_rules: []\n"
        "minimax_semantic_scoring_enabled: false\n"
        "waiver_file: " + str(tmp_path / "waivers.yaml") + "\n"
        "runtime_log_paths: []\n"
    )
    (tmp_path / "waivers.yaml").write_text("waivers: []\n")
    runner = CliRunner()
    result = runner.invoke(main, ["benchmark", "--config", str(cfg)])
    assert result.exit_code == 0
    assert "benchmark: ran" in result.output
    assert (tmp_path / "out" / "skill_scorecard.json").exists()


# ===========================================================================
# SCENARIO 3: `recommend` CLI command writes scorecard and prints count
# ===========================================================================
def test_recommend_command_writes_scorecard(tmp_path: Path):
    """The `recommend` CLI command writes the scorecard and prints count."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "skill_directories: []\n"
        "agent_directories: []\n"
        "output_directory: " + str(tmp_path / "out") + "\n"
        "token_thresholds: {high_cost: 8000}\n"
        "overlap_thresholds: {blocking: 60, warning: 40}\n"
        "roi_thresholds: {keep_min: 70, rewrite_min: 50, deprecate_max: 30}\n"
        "benchmark_thresholds: {default_minimum: 0.7}\n"
        "ci_blocking_rules: []\n"
        "minimax_semantic_scoring_enabled: false\n"
        "waiver_file: " + str(tmp_path / "waivers.yaml") + "\n"
        "runtime_log_paths: []\n"
    )
    (tmp_path / "waivers.yaml").write_text("waivers: []\n")
    runner = CliRunner()
    result = runner.invoke(main, ["recommend", "--config", str(cfg)])
    assert result.exit_code == 0
    assert "recommend:" in result.output
    assert (tmp_path / "out" / "skill_scorecard.json").exists()


# ===========================================================================
# SCENARIO 4: `rewrite` CLI command with no --artifact filter prints count
# ===========================================================================
def test_rewrite_command_without_artifact_filter(tmp_path: Path):
    """The `rewrite` CLI command without --artifact prints total count."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "skill_directories: []\n"
        "agent_directories: []\n"
        "output_directory: " + str(tmp_path / "out") + "\n"
        "token_thresholds: {high_cost: 8000}\n"
        "overlap_thresholds: {blocking: 60, warning: 40}\n"
        "roi_thresholds: {keep_min: 70, rewrite_min: 50, deprecate_max: 30}\n"
        "benchmark_thresholds: {default_minimum: 0.7}\n"
        "ci_blocking_rules: []\n"
        "minimax_semantic_scoring_enabled: false\n"
        "waiver_file: " + str(tmp_path / "waivers.yaml") + "\n"
        "runtime_log_paths: []\n"
    )
    (tmp_path / "waivers.yaml").write_text("waivers: []\n")
    runner = CliRunner()
    result = runner.invoke(main, ["rewrite", "--config", str(cfg)])
    assert result.exit_code == 0
    assert "rewrite: 0 proposed rewrite(s)" in result.output


# ===========================================================================
# SCENARIO 5: `rewrite` CLI command with --artifact filter prints filtered count
# ===========================================================================
def test_rewrite_command_with_artifact_filter(tmp_path: Path):
    """The `rewrite` CLI command with --artifact filters to one artifact."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "skill_directories: []\n"
        "agent_directories: []\n"
        "output_directory: " + str(tmp_path / "out") + "\n"
        "token_thresholds: {high_cost: 8000}\n"
        "overlap_thresholds: {blocking: 60, warning: 40}\n"
        "roi_thresholds: {keep_min: 70, rewrite_min: 50, deprecate_max: 30}\n"
        "benchmark_thresholds: {default_minimum: 0.7}\n"
        "ci_blocking_rules: []\n"
        "minimax_semantic_scoring_enabled: false\n"
        "waiver_file: " + str(tmp_path / "waivers.yaml") + "\n"
        "runtime_log_paths: []\n"
    )
    (tmp_path / "waivers.yaml").write_text("waivers: []\n")
    runner = CliRunner()
    result = runner.invoke(main, ["rewrite", "--config", str(cfg), "--artifact", "missing-skill"])
    assert result.exit_code == 0
    assert "rewrite: 0 rewrite(s) for missing-skill" in result.output


# ===========================================================================
# SCENARIO 6: _compute_health returns 100, 0 for an empty inventory
#
# Given: a PipelineResult with no inventory
# When:  _compute_health is called
# Then:  it returns (100, 0) — perfect health for an empty catalog
# ===========================================================================
def test_compute_health_returns_perfect_score_for_empty_inventory():
    """An empty inventory returns 100/100 health, 0 blocking."""
    from skill_governance.config_loader import GovernanceConfig
    cfg = GovernanceConfig(
        {
            "skill_directories": [],
            "agent_directories": [],
            "output_directory": "output",
            "token_thresholds": {"high_cost": 8000},
            "overlap_thresholds": {"blocking": 60, "warning": 40},
            "roi_thresholds": {"keep_min": 70, "rewrite_min": 50, "deprecate_max": 30},
            "benchmark_thresholds": {"default_minimum": 0.7},
            "ci_blocking_rules": [],
            "minimax_semantic_scoring_enabled": False,
            "waiver_file": "waivers.yaml",
            "runtime_log_paths": [],
        }
    )
    result = PipelineResult(
        started_at="2026-06-13T00:00:00Z",
        finished_at="2026-06-13T00:01:00Z",
        ci_passed=True,
    )
    score, blocking = _compute_health(result, [], cfg)
    assert score == 100, f"empty inventory should be 100/100, got {score}"
    assert blocking == 0, f"empty inventory should have 0 blocking, got {blocking}"
