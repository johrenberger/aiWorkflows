from __future__ import annotations

from dataclasses import asdict

from mutationctl.errors import ConfigError
from mutationctl.models import WorkflowConfig
from mutationctl.repo.intake import validate_repo_input

DEFAULTS = {
    "allow_commit": False,
    "allow_dependency_install": False,
    "allow_production_fixes": False,
    "allow_test_changes": False,
    "max_target_files": 5,
    "mutation_target_initial": 60,
    "mutation_target_mature": 75,
    "mode": "report",
}


def _parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return bool(value)


def load_workflow_config(raw_config):
    merged = {**DEFAULTS, **dict(raw_config)}
    repo_value = merged.get("repo")
    if not repo_value:
        raise ConfigError("A repository input is required")

    repo_input = validate_repo_input(str(repo_value))
    branch = merged.get("branch")
    mode = str(merged.get("mode", "report")).strip().lower()
    if mode not in {"report", "apply"}:
        raise ConfigError(f"Unsupported mode: {mode}")

    max_target_files = int(merged["max_target_files"])
    mutation_target_initial = int(merged["mutation_target_initial"])
    mutation_target_mature = int(merged["mutation_target_mature"])

    if not 0 <= mutation_target_initial <= 100:
        raise ConfigError("mutation_target_initial must be between 0 and 100")
    if not 0 <= mutation_target_mature <= 100:
        raise ConfigError("mutation_target_mature must be between 0 and 100")
    if mutation_target_initial > mutation_target_mature:
        raise ConfigError("mutation_target_initial must not exceed mutation_target_mature")
    if max_target_files <= 0:
        raise ConfigError("max_target_files must be positive")

    return WorkflowConfig(
        repo_url=repo_input.repo_url,
        repo_path=repo_input.repo_path,
        branch=str(branch).strip() if branch else None,
        mode=mode,
        allow_commit=_parse_bool(merged["allow_commit"]),
        allow_dependency_install=_parse_bool(merged["allow_dependency_install"]),
        allow_production_fixes=_parse_bool(merged["allow_production_fixes"]),
        allow_test_changes=_parse_bool(merged["allow_test_changes"]),
        max_target_files=max_target_files,
        mutation_target_initial=mutation_target_initial,
        mutation_target_mature=mutation_target_mature,
    )


def config_to_dict(config: WorkflowConfig) -> dict:
    return asdict(config)
