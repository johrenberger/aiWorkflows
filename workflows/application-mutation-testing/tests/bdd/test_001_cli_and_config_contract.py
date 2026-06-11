from __future__ import annotations

from mutationctl.cli import build_parser
from mutationctl.config import load_workflow_config
from mutationctl.errors import ConfigError


def test_given_cli_when_help_runs_then_expected_commands_are_listed() -> None:
    parser = build_parser()
    help_text = parser.format_help()

    for command in [
        "init",
        "detect",
        "ingest-coverage",
        "select-targets",
        "run-baseline",
        "classify-survivors",
        "harden-tests",
        "validate",
        "recheck",
        "render-ledger",
        "commit",
        "run",
    ]:
        assert command in help_text


def test_given_minimal_run_inputs_when_config_is_parsed_then_safety_defaults_apply() -> None:
    config = load_workflow_config(
        {
            "repo": "https://github.com/example/project",
        }
    )

    assert config.allow_commit is False
    assert config.allow_dependency_install is False
    assert config.allow_production_fixes is False
    assert config.allow_test_changes is False
    assert config.max_target_files == 5
    assert config.mutation_target_initial == 60
    assert config.mutation_target_mature == 75
    assert config.mode == "report"


def test_given_explicit_inputs_when_config_is_parsed_then_values_are_normalized() -> None:
    config = load_workflow_config(
        {
            "repo": "https://github.com/example/project.git",
            "branch": " feature/test-hardening ",
            "mode": " APPLY ",
            "max_target_files": "7",
            "mutation_target_initial": "61",
            "mutation_target_mature": "80",
            "allow_commit": True,
            "allow_dependency_install": True,
            "allow_production_fixes": True,
            "allow_test_changes": True,
        }
    )

    assert config.repo_url == "https://github.com/example/project"
    assert config.branch == "feature/test-hardening"
    assert config.mode == "apply"
    assert config.max_target_files == 7
    assert config.mutation_target_initial == 61
    assert config.mutation_target_mature == 80
    assert config.allow_commit is True


def test_given_invalid_thresholds_when_config_is_parsed_then_config_error_is_raised() -> None:
    try:
        load_workflow_config(
            {
                "repo": "https://github.com/example/project",
                "mutation_target_initial": 90,
                "mutation_target_mature": 80,
            }
        )
    except ConfigError:
        return

    raise AssertionError("Expected ConfigError for descending thresholds")
