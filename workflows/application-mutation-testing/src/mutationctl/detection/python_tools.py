from __future__ import annotations

from pathlib import Path

from mutationctl.models import MutationToolEvidence


def detect_mutmut(repo_path: Path) -> MutationToolEvidence | None:
    for filename in ["pyproject.toml", "requirements.txt", "requirements-dev.txt", "setup.cfg", "tox.ini"]:
        path = repo_path / filename
        if path.is_file() and "mutmut" in path.read_text(encoding="utf-8").lower():
            return MutationToolEvidence("mutmut", "python", True, False, None, [filename], [filename])
    return None
