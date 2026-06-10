from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path

from ..models import BranchRunRecord


def is_dirty(repo_path: str | Path) -> bool:
    result = subprocess.run(["git", "status", "--short"], cwd=repo_path, capture_output=True, text=True)
    return bool(result.stdout.strip())


def create_branch(repo_path: str | Path, module: str, branch_prefix: str = "test-automation-v2", allow_dirty: bool = False) -> BranchRunRecord:
    repo_path = Path(repo_path)
    dirty = is_dirty(repo_path)
    if dirty and not allow_dirty:
        raise RuntimeError("working tree is dirty")
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    branch_name = f"{branch_prefix}/{timestamp}-{module.replace('/', '-')}"
    result = subprocess.run(["git", "checkout", "-b", branch_name], cwd=repo_path, capture_output=True, text=True)
    created = result.returncode == 0
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_path, capture_output=True, text=True).stdout.strip() if created else ""
    return BranchRunRecord(branch_name=branch_name, module=module, created=created, dirty=dirty, sha=sha)

