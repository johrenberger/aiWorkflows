"""Tests for storage migration of public_signatures column (PR #29 - Bug #9)."""
import sqlite3
import sys
from pathlib import Path


def test_fresh_db_has_public_signatures_column(tmp_path):
    """A fresh DB should have the public_signatures column."""
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from test_factory.storage import Storage
    s = Storage(tmp_path / "fresh.sqlite")
    cols = {row[1] for row in s.conn.execute("PRAGMA table_info(work_items)").fetchall()}
    assert "public_signatures" in cols, "fresh DB missing public_signatures column"
    # Default value should be empty list
    rows = list(s.conn.execute("SELECT public_signatures FROM work_items"))
    assert all(row[0] == "[]" for row in rows) or len(rows) == 0
    s.close()


def test_migration_adds_public_signatures_to_old_db(tmp_path):
    """An existing DB (pre-PR-#29) should be migrated to add the column."""
    sys.path.insert(0, str(Path(__file__).parent.parent))
    # Create a pre-existing DB without the column
    db_path = tmp_path / "old.sqlite"
    conn = sqlite3.connect(str(db_path))
    old_schema = """
    CREATE TABLE IF NOT EXISTS work_items (
      work_item_id TEXT PRIMARY KEY,
      source_path TEXT NOT NULL,
      language TEXT NOT NULL,
      module TEXT NOT NULL,
      current_line_coverage REAL NOT NULL DEFAULT 0,
      current_branch_coverage REAL,
      uncovered_lines TEXT NOT NULL DEFAULT \'[]\',
      uncovered_branches TEXT NOT NULL DEFAULT \'[]\',
      risk_score REAL NOT NULL DEFAULT 0,
      risk_factors TEXT NOT NULL DEFAULT \'{}\',
      existing_test_files TEXT NOT NULL DEFAULT \'[]\',
      recommended_test_type TEXT NOT NULL DEFAULT \'unit\',
      supporting_files TEXT NOT NULL DEFAULT \'[]\',
      conventions_summary TEXT NOT NULL DEFAULT \'\',
      validation_command TEXT NOT NULL DEFAULT \'\',
      acceptance_criteria TEXT NOT NULL DEFAULT \'[]\',
      status TEXT NOT NULL DEFAULT \'pending\',
      priority REAL NOT NULL DEFAULT 0,
      content_path TEXT NOT NULL DEFAULT \'\',
      validated_files TEXT NOT NULL DEFAULT \'[]\',
      validation_repo_sha TEXT NOT NULL DEFAULT \'\',
      validation_reason TEXT NOT NULL DEFAULT \'\',
      validation_report_path TEXT NOT NULL DEFAULT \'\'
    );
    """
    conn.executescript(old_schema)
    conn.commit()
    conn.close()
    # Verify it doesn't have the column yet
    conn = sqlite3.connect(str(db_path))
    cols = {row[1] for row in conn.execute("PRAGMA table_info(work_items)").fetchall()}
    assert "public_signatures" not in cols
    conn.close()
    # Now open with v2 storage
    from test_factory.storage import Storage
    s = Storage(str(db_path))
    cols = {row[1] for row in s.conn.execute("PRAGMA table_info(work_items)").fetchall()}
    assert "public_signatures" in cols, "migration did not add public_signatures column"
    s.close()


def test_upsert_work_item_persists_public_signatures(tmp_path):
    """A work-item with public_signatures should be persisted to SQLite."""
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from test_factory.models import WorkItemRecord
    from test_factory.storage import Storage
    s = Storage(str(tmp_path / "persist.sqlite"))
    item = WorkItemRecord(
        work_item_id="wi-test123",
        source_path="src/foo.py",
        language="python",
        module="src",
        current_line_coverage=0.0,
        current_branch_coverage=None,
        public_signatures=["bar", "baz", "qux"],
    )
    s.upsert_work_item(item)
    # Read back
    row = s.get_work_item("wi-test123")
    assert row is not None
    import json
    persisted = json.loads(row["public_signatures"])
    assert persisted == ["bar", "baz", "qux"]
    s.close()


def test_risk_scores_includes_language_field():
    """Bug #32: test_gap_queue items had no `language` field, forcing the
    LLM to guess language from path extensions. RiskScoreRecord now
    carries the language, persisted via SQLite and serialized to JSON."""
    from test_factory.models import RiskScoreRecord
    rec = RiskScoreRecord(
        path="src/main/java/com/example/Foo.java",
        module="example",
        line_coverage=0.0,
        branch_coverage=None,
        language="java",
    )
    assert rec.language == "java"
    # asdict should expose it (this is what gets serialized to the queue)
    from dataclasses import asdict
    data = asdict(rec)
    assert data["language"] == "java"
