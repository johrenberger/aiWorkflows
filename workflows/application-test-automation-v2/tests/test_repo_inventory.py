from __future__ import annotations

from test_factory.analyzers.repo_inventory import inventory_repo
from test_factory.models import Config


def test_inventory_prunes_excluded_directories_and_large_files(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "src").mkdir()
    (repo / "node_modules").mkdir()
    (repo / "src" / "app.py").write_text("def run():\n    return True\n", encoding="utf-8")
    (repo / "node_modules" / "ignored.js").write_text("console.log('ignored')\n", encoding="utf-8")
    (repo / "large.py").write_text("x" * 64, encoding="utf-8")
    config = Config(max_source_file_chars=32)

    files, exclusions = inventory_repo(repo, config)

    assert any(record.path == "src/app.py" for record in files)
    assert all(record.path != "node_modules/ignored.js" for record in files)
    assert any(item["path"] == "node_modules" and item["reason"] == "excluded-glob" for item in exclusions)
    assert any(item["path"] == "large.py" and item["reason"] == "large-file" for item in exclusions)
