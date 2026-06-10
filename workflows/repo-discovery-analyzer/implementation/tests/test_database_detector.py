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


# --- Java entity name extraction regression tests ---
# These cover the bug we hit on johrenberger/BroadleafCommerce:
# `_java_entity_name` previously used a regex that matched the FIRST
# `class IDENT` in the file, including `class` inside Javadoc comments
# and string literals. For files like MergePersistenceUnitManager.java
# where the Javadoc says "Merges jars, class names and mapping files"
# the previous regex captured `names` instead of the actual class.
from repo_discovery_analyzer.detectors.database import (  # noqa: E402
    _java_entity_name,
)


JAVA_BROADLEAF_PATTERN = """
/*-
 * #%L
 * BroadleafCommerce Common Libraries
 * %%
 * Copyright (C) 2009 - 2026 Broadleaf Commerce
 * Licensed under the Broadleaf Fair Use License.
 * #L%
 */
package org.broadleafcommerce.common.extensibility.jpa;

import jakarta.persistence.spi.PersistenceUnitInfo;

/**
 * Merges jars, class names and mapping file names from several persistence.xml files. The
 * MergePersistenceUnitManager will continue to keep track of individual persistence unit
 * names (including individual data sources). When a specific PersistenceUnitInfo is requested
 * by unit name, the appropriate PersistenceUnitInfo is returned with modified jar files
 * urls, class names and mapping file names that include the comprehensive collection of these
 * values from all persistence.xml files.
 *
 * @author jfischer, jjacobs
 */
@Entity
public class MergePersistenceUnitManager extends DefaultPersistenceUnitManager {

    private static final Log LOG = LogFactory.getLog(MergePersistenceUnitManager.class);
    public static String currentProcessingPersistenceUnit;

    @PostConstruct
    public void afterPropertiesSet() throws Exception {
        // do something with class names and mapping file names internally
        String classNames = "my class names and other things";
    }
}
"""


def test_java_entity_name_skips_javadoc_class_keyword():
    """Regression for johrenberger/BroadleafCommerce: Javadoc containing
    the word 'class' (e.g. 'class names') must not be matched."""
    name = _java_entity_name(JAVA_BROADLEAF_PATTERN, "MergePersistenceUnitManager.java")
    assert name == "MergePersistenceUnitManager", (
        f"expected the real class name, got {name!r}"
    )


def test_java_entity_name_skips_string_literal_class_keyword():
    """A `class` keyword inside a string literal (e.g. `LOG = LogFactory.getLog(MergePersistenceUnitManager.class)`)
    must not be matched as the entity name."""
    text = (
        '@Entity\n'
        'public class Foo {\n'
        '  private static final Log LOG = LogFactory.getLog(Foo.class);\n'
        '  public void bar() { "class with no entity" /* not a class */ }\n'
        '}\n'
    )
    name = _java_entity_name(text, "Foo.java")
    assert name == "Foo"


def test_java_entity_name_falls_back_to_filename_when_no_class():
    """Kotlin or annotation-only files (no `class` keyword) should fall back to
    the file stem rather than returning an empty string or crashing."""
    text = "@Entity\ndata class Bar(val x: Int)\n"
    # Strictly the regex would still find `class Bar`, but the file has a leading-
    # lowercase Kotlin-style name; the fallback to filename is what we want when
    # no uppercase class is found.
    name = _java_entity_name("", "NoClassHere.java")
    assert name == "NoClassHere"


def test_java_entity_name_handles_modifiers_and_annotations():
    text = """
    @Entity
    @Table(name = "widgets")
    public final class WidgetImpl implements Widget {
    }
    """
    assert _java_entity_name(text, "WidgetImpl.java") == "WidgetImpl"


def test_java_entity_name_ignores_inner_classes_with_lowercase_after():
    """If for some reason the file has a `class` keyword whose identifier
    is a Java reserved word (e.g. `class names` from a Javadoc), the regex
    must skip it and find the real class."""
    text = """
    /** see class names and class is and class and */
    @Entity
    public class RealEntity {}
    """
    assert _java_entity_name(text, "RealEntity.java") == "RealEntity"


# --- Comment/string stripping edge cases ---
# These exercise the corner cases of _strip_java_comments_and_strings that
# the entity-name test alone doesn't hit: unterminated comments/strings,
# escape sequences inside string/char literals, char literals, etc.
from repo_discovery_analyzer.detectors.database import (  # noqa: E402
    _strip_java_comments_and_strings,
)


def test_strip_handles_unterminated_block_comment():
    """A `/*` with no closing `*/` should consume the rest of the file."""
    text = "/* unterminated comment with class names\npublic class Real {}"
    out = _strip_java_comments_and_strings(text)
    # Block-comment body is blanked; the entire file is consumed by the
    # unterminated block comment, so no class survives.
    assert "class" not in out


def test_strip_handles_unterminated_line_comment_at_eof():
    text = "// comment with class names that never ends"
    out = _strip_java_comments_and_strings(text)
    # Line-comment body blanked; 'class' token is still inside the comment.
    assert "class" not in out


def test_strip_handles_escape_in_string_literal():
    """A backslash inside a string literal must not be confused with the
    closing quote."""
    text = '@Entity\npublic class Real {\n  String s = "class with \\" escaped quote";\n}\n'
    out = _strip_java_comments_and_strings(text)
    # Body of the string should be blanked.
    assert 'class with' not in out
    # The `class Real` declaration is outside the string, should survive.
    assert "class Real" in out


def test_strip_handles_escape_in_char_literal():
    """A backslash inside a char literal must not be confused with the
    closing quote."""
    text = "@Entity\npublic class Real {\n  char c = '\\\\';\n}\n"
    out = _strip_java_comments_and_strings(text)
    assert "class Real" in out
    # The two backslash chars in the char literal body are blanked to spaces.
    assert "'  '" in out


def test_strip_handles_unterminated_char_literal():
    """A `'` with no closing quote before a newline should not eat the
    rest of the file."""
    text = "@Entity\npublic class Real {\n  char c = 'x\n}\n"
    out = _strip_java_comments_and_strings(text)
    assert "class Real" in out


def test_strip_handles_unterminated_string_with_newline():
    """A `"` without a closing quote before a newline should not eat the
    rest of the file."""
    text = '@Entity\npublic class Real {\n  String s = "unterminated\n  String s2 = "ok";\n}\n'
    out = _strip_java_comments_and_strings(text)
    # The unterminated string is consumed up to the newline; the rest of
    # the file (including the second string and its body) is preserved.
    assert "class Real" in out
    # The body of the unterminated string is blanked.
    assert "unterminated" not in out


def test_strip_handles_char_literal():
    text = "@Entity\npublic class Real {\n  char c = 'a';\n}\n"
    out = _strip_java_comments_and_strings(text)
    # Char literal body is blanked to whitespace.
    assert "class Real" in out
    # Verify the char literal body was blanked: position of `'a'` becomes spaces.
    assert "' '" in out


def test_strip_returns_input_when_no_comments():
    text = "public class Real {}"
    out = _strip_java_comments_and_strings(text)
    # No whitespace-only substitutions: every char survives unchanged.
    assert out == text
