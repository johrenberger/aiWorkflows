from __future__ import annotations

from pathlib import Path

from mutationctl.models import MutationToolEvidence


def detect_go_tool(repo_path: Path) -> MutationToolEvidence:
    evidence = ["go.mod"] if (repo_path / "go.mod").is_file() else []
    return MutationToolEvidence("go-mutesting", "go", False, True, None, [], evidence, "Detection is scaffolded only")
