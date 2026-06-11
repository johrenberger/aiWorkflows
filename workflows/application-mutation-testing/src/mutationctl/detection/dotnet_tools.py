from __future__ import annotations

from pathlib import Path

from mutationctl.models import MutationToolEvidence


def detect_dotnet_tool(repo_path: Path) -> MutationToolEvidence:
    projects = sorted(path.name for path in repo_path.glob("*.csproj"))
    return MutationToolEvidence(
        "stryker-dotnet", "dotnet", False, True, None, projects, projects, "Detection is scaffolded only"
    )
