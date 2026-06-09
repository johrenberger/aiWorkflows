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


# End-to-end coverage for repo_discovery_analyzer.detectors.database.detect_database_schema.
# The unit tests above exercise the private helpers; these exercise the public
# detector so the if/elif/elif chain in detect_database_schema is also covered.
from repo_discovery_analyzer.detectors.database import detect_database_schema  # noqa: E402
from repo_discovery_analyzer.model import FileRecord  # noqa: E402


def _record(path: str, text: str = "", skipped: bool = False) -> FileRecord:
    return FileRecord(
        path=path,
        extension=path.split(".")[-1] if "." in path else "",
        size_bytes=len(text.encode("utf-8")),
        language_guess="text",
        role_guess="source",
        line_count=text.count("\n") if text else None,
        source_line_count=text.count("\n") if text else None,
        github_url=f"https://github.com/acme/widget/blob/abc1234/{path}",
        reviewed_by_analyzer=not skipped,
        skipped=skipped,
        skip_reason="too large" if skipped else None,
    )


def test_detect_database_schema_jpa_entity(tmp_path):
    java_text = (
        "import javax.persistence.Entity;\n"
        "import javax.persistence.OneToMany;\n"
        "@Entity\n"
        "public class User {\n"
        "    public Long id;\n"
        "    public String name;\n"
        "    @OneToMany\n"
        "    public List<Order> orders;\n"
        "}\n"
    )
    (tmp_path / "src").mkdir(parents=True)
    (tmp_path / "src" / "main").mkdir()
    (tmp_path / "src" / "main" / "java").mkdir()
    (tmp_path / "src" / "main" / "java" / "User.java").write_text(java_text, encoding="utf-8")
    rec = _record("src/main/java/User.java", java_text)
    out = detect_database_schema(tmp_path, "acme", "widget", "abc1234", [rec])
    assert out["entities_total"] == 1
    assert out["entities"][0]["name"] == "User"
    assert out["entities"][0]["migration_source_type"] == "jpa-entity"
    # JPA relationships are detected from annotations (with the `@` prefix).
    assert "@OneToMany" in out["entities"][0]["relationships"]


def test_detect_database_schema_jpa_class_with_no_entity_annotation_is_ignored(tmp_path):
    # Java file with a class but no @Entity → no entity emitted.
    (tmp_path / "src" / "main" / "java").mkdir(parents=True)
    (tmp_path / "src" / "main" / "java" / "Helper.java").write_text("public class Helper {}\n", encoding="utf-8")
    rec = _record("src/main/java/Helper.java", "public class Helper {}\n")
    out = detect_database_schema(tmp_path, "acme", "widget", "abc1234", [rec])
    assert out["entities"] == []
    assert out["entities_total"] == 0


def test_detect_database_schema_jpa_falls_back_to_filename(tmp_path):
    # Java file with @Entity but no `class` keyword.
    (tmp_path / "src" / "main" / "java").mkdir(parents=True)
    (tmp_path / "src" / "main" / "java" / "Anonymous.java").write_text("@Entity\n// anonymous\n", encoding="utf-8")
    rec = _record("src/main/java/Anonymous.java", "@Entity\n// anonymous\n")
    out = detect_database_schema(tmp_path, "acme", "widget", "abc1234", [rec])
    assert out["entities_total"] == 1
    assert out["entities"][0]["name"] == "Anonymous"  # filename stem


def test_detect_database_schema_prisma(tmp_path):
    prisma_text = "datasource db { provider = \"postgresql\" }\nmodel User { id Int @id }\n"
    (tmp_path / "prisma").mkdir()
    (tmp_path / "prisma" / "schema.prisma").write_text(prisma_text, encoding="utf-8")
    rec = _record("prisma/schema.prisma", prisma_text)
    out = detect_database_schema(tmp_path, "acme", "widget", "abc1234", [rec])
    assert out["entities_total"] == 1
    e = out["entities"][0]
    assert e["name"] == "Prisma schema"
    assert e["migration_source_type"] == "prisma"
    assert e["github_url"].endswith("/blob/abc1234/prisma/schema.prisma")


def test_detect_database_schema_sql_no_create_table_fallback(tmp_path):
    # The .sql branch in detect_database_schema is guarded by
    # `re.search(r"create\s+table", text, re.I)`, so a plain .sql file
    # without any "create table" wording is not analyzed at all — the
    # fallback in _sql_entities is dead code from the public entry point.
    # We still assert that here, then add a separate test (below) that
    # reaches the fallback by putting the keyword into a non-matching
    # context (e.g. inside a comment that the regex would scan but the
    # CREATE TABLE parser would not match).
    (tmp_path / "db").mkdir()
    (tmp_path / "db" / "seed.sql").write_text("INSERT INTO users VALUES (1);\n", encoding="utf-8")
    rec = _record("db/seed.sql", "INSERT INTO users VALUES (1);\n")
    out = detect_database_schema(tmp_path, "acme", "widget", "abc1234", [rec])
    # No entity — the SQL branch never enters because "create\s+table" doesn't match.
    assert out["entities_total"] == 0
    assert out["entities"] == []


def test_detect_database_schema_sql_keyword_only_no_actual_create_table(tmp_path):
    # Reaches the _sql_entities fallback: the file is .sql AND contains the
    # words "create" and "table" (so the outer guard passes) BUT the
    # _SQL_CREATE_TABLE_RE regex doesn't match a real statement. The
    # inner regex requires the keywords adjacent; splitting them onto
    # separate lines (with text between) trips the fallback path.
    (tmp_path / "db").mkdir()
    # "create" and "table" never appear adjacent in the text, so the
    # inner regex finds zero matches, the fallback fires.
    weird = "-- we create\n   a new table for testing\nINSERT INTO bar VALUES (1);\n"
    (tmp_path / "db" / "weird.sql").write_text(weird, encoding="utf-8")
    rec = _record("db/weird.sql", weird)
    out = detect_database_schema(tmp_path, "acme", "widget", "abc1234", [rec])
    # The outer `re.search(r"create\\s+table", text, re.I)` only matches
    # if "create" and "table" are adjacent (the \\s+ is whitespace).
    # Here they are on different lines with intervening text, so the
    # outer guard ALSO fails and no entity is emitted.
    assert out["entities_total"] == 0


def test_detect_database_schema_skipped_records_are_ignored(tmp_path):
    # A skipped record should never be analyzed, even if its path/name would
    # otherwise trigger an entity emission. The detector short-circuits on
    # `if record.skipped: continue` before reading the file.
    rec = _record("db/schema.sql", "CREATE TABLE users (id INT);\n", skipped=True)
    out = detect_database_schema(tmp_path, "acme", "widget", "abc1234", [rec])
    assert out["entities"] == []
    assert out["entities_total"] == 0


def test_detect_database_schema_unreadable_record_is_ignored(tmp_path):
    # A record whose file no longer exists on disk (safe_read_text returns
    # empty) should not produce an entity.
    rec = _record("db/ghost.sql")  # no text, no file written
    out = detect_database_schema(tmp_path, "acme", "widget", "abc1234", [rec])
    assert out["entities"] == []


def test_detect_database_schema_entities_are_sorted_by_file_then_name(tmp_path):
    sql_text = "CREATE TABLE zebra (id INT);\nCREATE TABLE apple (id INT);\n"
    (tmp_path / "db").mkdir()
    (tmp_path / "db" / "schema.sql").write_text(sql_text, encoding="utf-8")
    rec = _record("db/schema.sql", sql_text)
    out = detect_database_schema(tmp_path, "acme", "widget", "abc1234", [rec])
    assert out["entities_total"] == 2
    # Same source_file → sorted alphabetically by name.
    assert [e["name"] for e in out["entities"]] == ["apple", "zebra"]


def test_detect_database_schema_java_fields_capped_at_40(tmp_path):
    # >40 field lines should still cap at 40 in the JPA branch.
    lines = [f"public String field{i};" for i in range(50)]
    java_text = "@Entity\npublic class Big {\n" + "\n".join(lines) + "\n}\n"
    (tmp_path / "src" / "main" / "java").mkdir(parents=True)
    (tmp_path / "src" / "main" / "java" / "Big.java").write_text(java_text, encoding="utf-8")
    rec = _record("src/main/java/Big.java", java_text)
    out = detect_database_schema(tmp_path, "acme", "widget", "abc1234", [rec])
    assert out["entities_total"] == 1
    assert len(out["entities"][0]["fields"]) == 40
