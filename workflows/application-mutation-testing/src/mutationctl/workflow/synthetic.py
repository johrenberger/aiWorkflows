from __future__ import annotations

import shutil
from pathlib import Path


def prepare_synthetic_repo(source: str | Path, workspace: str | Path) -> Path:
    source_path = Path(source).resolve()
    destination = Path(workspace).resolve() / "synthetic-repo"
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source_path, destination)
    return destination
