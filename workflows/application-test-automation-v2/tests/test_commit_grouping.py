from __future__ import annotations

import subprocess

from test_factory.git.commit_manager import commit_module


def test_module_commit_grouping(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "module-a").mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True, text=True)
    (repo / "module-a" / "a.txt").write_text("hello", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True, capture_output=True, text=True)
    (repo / "module-a" / "b.txt").write_text("world", encoding="utf-8")
    record = commit_module(repo, "module-a", "test: improve coverage for module-a")
    assert record.message.startswith("test: improve coverage")
