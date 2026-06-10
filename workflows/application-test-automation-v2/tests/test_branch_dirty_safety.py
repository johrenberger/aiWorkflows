from __future__ import annotations

import shutil
import subprocess

from test_factory.git.branch_manager import is_dirty


def test_dirty_tree_detection(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    (repo / "file.txt").write_text("hello", encoding="utf-8")
    assert is_dirty(repo)
