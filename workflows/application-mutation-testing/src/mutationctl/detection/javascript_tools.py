from __future__ import annotations

import json
from pathlib import Path

from mutationctl.models import MutationToolEvidence


def detect_stryker(repo_path: Path) -> MutationToolEvidence | None:
    package_json = repo_path / "package.json"
    config_files = [name for name in ["stryker.conf.json", "stryker.conf.js"] if (repo_path / name).is_file()]
    if package_json.is_file():
        data = json.loads(package_json.read_text(encoding="utf-8"))
        dependencies = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
        version = dependencies.get("@stryker-mutator/core")
        if version is not None:
            return MutationToolEvidence(
                "stryker", "javascript", True, False, str(version), config_files, ["package.json", *config_files]
            )
    if config_files:
        return MutationToolEvidence("stryker", "javascript", True, False, None, config_files, config_files)
    return None
