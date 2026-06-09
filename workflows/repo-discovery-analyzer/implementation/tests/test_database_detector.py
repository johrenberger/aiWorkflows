"""Tests for the SQL schema detector in repo_discovery_analyzer.detectors.database.

These exercise the regression we hit on johrenberger/creative-ai:
"CREATE TABLE IF NOT EXISTS ..." was being parsed as a single entity
named "IF" with every line of the file treated as its fields.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make the implementation importable when tests are run from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from repo_discovery_analyzer.detectors.database import (  # noqa: E402
    _sql_entities,
    _sql_fields,
    _sql_relationships,
)


CREATIVE_AI_SCHEMA = """
-- creative-ai db/schema.sql (trimmed, verbatim pattern from real file)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_token TEXT UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    status TEXT DEFAULT 'pending'
);
"""


def test_sql_entities_one_per_create_table():
    ents = _sql_entities(CREATIVE_AI_SCHEMA, "db/schema.sql", "https://x/db/schema.sql")
    names = [e["name"] for e in ents]
    assert names == ["users", "sessions", "tasks"], f"got {names!r}"


def test_sql_entity_names_skip_if_not_exists_keyword():
    """The original bug: 'CREATE TABLE IF NOT EXISTS' captured name='IF'."""
    ents = _sql_entities(CREATIVE_AI_SCHEMA, "db/schema.sql", "")
    for e in ents:
        assert e["name"] != "IF", f"entity name leaked 'IF': {e}"
        assert e["name"].isidentifier(), f"non-identifier name: {e['name']!r}"


def test_sql_fields_are_scoped_to_their_own_table():
    """Regression: previously every column-shaped line in the file was attributed
    to the first entity, so 'users' fields included columns from later tables."""
    ents = _sql_entities(CREATIVE_AI_SCHEMA, "db/schema.sql", "")
    by_name = {e["name"]: e for e in ents}

    users_fields = by_name["users"]["fields"]
    assert "username TEXT UNIQUE NOT NULL" in users_fields
    assert "session_token TEXT UNIQUE NOT NULL" not in users_fields, (
        "users leaked fields from sessions"
    )
    assert "title TEXT NOT NULL" not in users_fields, (
        "users leaked fields from tasks"
    )

    sessions_fields = by_name["sessions"]["fields"]
    assert "session_token TEXT UNIQUE NOT NULL" in sessions_fields
    assert "username TEXT UNIQUE NOT NULL" not in sessions_fields
    assert "title TEXT NOT NULL" not in sessions_fields


def test_sql_relationships_collected_from_foreign_keys():
    ents = _sql_entities(CREATIVE_AI_SCHEMA, "db/schema.sql", "")
    by_name = {e["name"]: e for e in ents}
    assert by_name["sessions"]["relationships"] == ["users"]
    # Tables with no FK emit an empty list, not None.
    assert by_name["users"]["relationships"] == []
    assert by_name["tasks"]["relationships"] == []


def test_sql_falls_back_to_filename_when_no_create_table():
    body = "INSERT INTO foo VALUES (1); -- no DDL here"
    ents = _sql_entities(body, "db/seed.sql", "")
    assert len(ents) == 1
    assert ents[0]["name"] == "seed"
    assert ents[0]["confidence"] == "low"
    assert ents[0]["fields"] == []


def test_sql_fields_handles_table_level_directives():
    body = """
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    PRIMARY KEY (id),
    UNIQUE(name),
    CONSTRAINT fk_x FOREIGN KEY (id) REFERENCES other(id)
    """
    fields = _sql_fields(body)
    # Column lines kept; table-level directives dropped.
    assert any("id INTEGER" in f for f in fields)
    assert any("name TEXT NOT NULL" in f for f in fields)
    assert not any(f.upper().startswith("PRIMARY KEY") for f in fields)
    assert not any(f.upper().startswith("UNIQUE") for f in fields)
    assert not any(f.upper().startswith("CONSTRAINT") for f in fields)


def test_sql_fields_ignores_blank_and_continuation_lines():
    body = """
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,

    created_at DATETIME
    """
    fields = _sql_fields(body)
    assert len(fields) == 3
    assert all(f.strip() for f in fields)
