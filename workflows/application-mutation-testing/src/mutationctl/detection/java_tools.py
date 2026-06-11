from __future__ import annotations

from pathlib import Path

from mutationctl.models import MutationToolEvidence


def detect_pit(repo_path: Path) -> MutationToolEvidence | None:
    for filename in ["pom.xml", "build.gradle"]:
        path = repo_path / filename
        if path.is_file():
            text = path.read_text(encoding="utf-8").lower()
            if "pitest" in text or "org.pitest" in text:
                return MutationToolEvidence("pit", "java", True, False, None, [filename], [filename])
    return None
