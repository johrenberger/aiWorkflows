from __future__ import annotations

import re
from pathlib import Path

from ..io_utils import DEFAULT_MAX_SUMMARY_ITEMS, safe_read_text
from ..model import FileRecord


def detect_database_schema(repo_path: Path, owner: str, repo: str, commit: str, records: list[FileRecord]) -> dict:
    entities: list[dict] = []
    total_count = 0

    def add(entity: dict) -> None:
        nonlocal total_count
        total_count += 1
        if len(entities) < DEFAULT_MAX_SUMMARY_ITEMS:
            entities.append(entity)

    for record in records:
        if record.skipped:
            continue
        text, _ = safe_read_text(repo_path / record.path)
        if not text:
            continue
        if record.path.endswith(".java") and "@Entity" in text:
            add(
                {
                    "name": _java_entity_name(text, record.path),
                    "source_file": record.path,
                    "github_url": record.github_url,
                    "fields": _java_fields(text),
                    "relationships": _java_relationships(text),
                    "migration_source_type": "jpa-entity",
                    "confidence": "high",
                }
            )
        if record.path.endswith(".sql") and re.search(r"create\s+table", text, re.I):
            for entity in _sql_entities(text, record.path, record.github_url):
                add(entity)
        if record.path.endswith("schema.prisma"):
            add(
                {
                    "name": "Prisma schema",
                    "source_file": record.path,
                    "github_url": record.github_url,
                    "fields": _sql_fields(text),
                    "relationships": [],
                    "migration_source_type": "prisma",
                    "confidence": "high",
                }
            )
    entities = sorted(entities, key=lambda x: (x["source_file"], x["name"]))
    return {
        "entities": entities,
        "entities_total": total_count,
        "entities_truncated": total_count > len(entities),
    }


def _java_entity_name(text: str, path: str) -> str:
    """Find the top-level class name in a Java source file.

    Returns the first class IDENT that looks like a top-level declaration.
    Real Java class names start with an uppercase letter, and the real
    declaration is not inside a comment or string literal — so we strip
    comments and string contents first, then look for the first identifier
    after a `class` keyword. This avoids the false-positive we hit on
    johrenberger/BroadleafCommerce where a Javadoc phrase like
    "* Merges jars, class names and mapping files" caused the previous
    regex to capture `names` instead of the real class name 9 lines later.

    Falls back to the filename stem when no class is found (e.g. Kotlin
    files with @Entity annotations, or annotation-only files).
    """
    stripped = _strip_java_comments_and_strings(text)
    m = re.search(r"class\s+([A-Za-z_][A-Za-z0-9_]*)", stripped)
    if m and m.group(1)[0].isupper():
        return m.group(1)
    return Path(path).stem


def _strip_java_comments_and_strings(text: str) -> str:
    """Replace the contents of /* */, // comments, and "string"/'char' literals
    with whitespace of equal length so byte offsets and line numbers are
    preserved. Used to keep regex search anchored outside of comment/string
    contexts that may legitimately contain the keyword we're looking for."""
    out = list(text)
    i = 0
    n = len(out)
    while i < n:
        c = out[i]
        # Block comment /* ... */
        if c == "/" and i + 1 < n and out[i + 1] == "*":
            j = text.find("*/", i + 2)
            if j == -1:
                for k in range(i, n):
                    if not out[k].isspace():
                        out[k] = " "
                break
            for k in range(i, j + 2):
                if not out[k].isspace():
                    out[k] = " "
            i = j + 2
            continue
        # Line comment // ...
        if c == "/" and i + 1 < n and out[i + 1] == "/":
            j = text.find("\n", i + 2)
            if j == -1:
                for k in range(i, n):
                    if not out[k].isspace():
                        out[k] = " "
                break
            for k in range(i, j):
                if not out[k].isspace():
                    out[k] = " "
            i = j
            continue
        # String literal "..."
        if c == '"':
            j = i + 1
            while j < n:
                if out[j] == "\\" and j + 1 < n:
                    if not out[j].isspace():
                        out[j] = " "
                    if not out[j + 1].isspace():
                        out[j + 1] = " "
                    j += 2
                    continue
                if out[j] == '"':
                    j += 1
                    break
                if out[j] == "\n":
                    break
                if not out[j].isspace():
                    out[j] = " "
                j += 1
            i = j
            continue
        # Char literal '...'
        if c == "'":
            j = i + 1
            while j < n:
                if out[j] == "\\" and j + 1 < n:
                    if not out[j].isspace():
                        out[j] = " "
                    if not out[j + 1].isspace():
                        out[j + 1] = " "
                    j += 2
                    continue
                if out[j] == "'":
                    j += 1
                    break
                if out[j] == "\n":
                    break
                if not out[j].isspace():
                    out[j] = " "
                j += 1
            i = j
            continue
        i += 1
    return "".join(out)


def _java_fields(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if re.search(r"\b(private|public|protected)\b.+;", line)][:40]


def _java_relationships(text: str) -> list[str]:
    return [needle for needle in ("@OneToMany", "@ManyToOne", "@ManyToMany", "@OneToOne") if needle in text]


# Matches one CREATE TABLE statement (anywhere in the file), tolerating:
#   - optional IF NOT EXISTS (which previously tripped the table-name capture)
#   - optional backticks / double-quotes around the name
#   - newlines inside the parens (re.DOTALL)
# The name capture is group 1; the body is group 2.
_SQL_CREATE_TABLE_RE = re.compile(
    r"create\s+table"
    r"(?:\s+if\s+not\s+exists)?"
    r"\s+`?\"?([A-Za-z0-9_]+)`?\"?"
    r"\s*\((.*?)\)"
    r"\s*(?:;|$)",
    re.IGNORECASE | re.DOTALL,
)

# Lines that look like column definitions: identifier [identifier...] then comma.
_SQL_FIELD_LINE_RE = re.compile(r"^\s*[`\"]?([A-Za-z_][A-Za-z0-9_]*)[`\"]?\s+[A-Za-z]")
_SQL_FK_RE = re.compile(
    r"foreign\s+key\s*\([^)]+\)\s*references\s+`?\"?([A-Za-z0-9_]+)`?\"?",
    re.IGNORECASE,
)


def _sql_entities(text: str, path: str, github_url: str) -> list[dict]:
    """Return one entity per CREATE TABLE statement found in `text`.

    Previously the detector emitted a single entity per .sql file and grabbed
    the wrong table name ("IF" from "CREATE TABLE IF NOT EXISTS ...") because
    the regex captured whatever token followed "CREATE TABLE". It also dumped
    every column-shaped line from the whole file into that one entity, so
    fields from later tables leaked into the first one. This iterates per
    statement instead and scopes fields/relationships to the table's own body.
    """
    entities: list[dict] = []
    for match in _SQL_CREATE_TABLE_RE.finditer(text):
        name = match.group(1)
        body = match.group(2)
        entities.append(
            {
                "name": name,
                "source_file": path,
                "github_url": github_url,
                "fields": _sql_fields(body),
                "relationships": _sql_relationships(body),
                "migration_source_type": "sql",
                "confidence": "high",
            }
        )
    if not entities:
        # Fall back to a single, deliberately generic entity so the analyzer
        # still reports something for SQL files that don't follow the
        # CREATE TABLE (...) convention (e.g. .sql dumps with INSERTs only).
        entities.append(
            {
                "name": Path(path).stem,
                "source_file": path,
                "github_url": github_url,
                "fields": [],
                "relationships": [],
                "migration_source_type": "sql",
                "confidence": "low",
            }
        )
    return entities


def _sql_fields(body: str) -> list[str]:
    """Extract column lines from inside a single CREATE TABLE body.

    `body` is the text between the parentheses of one CREATE TABLE statement.
    We accept the first 50 column-shaped lines, dropping table-level
    directives (CONSTRAINT, PRIMARY KEY, FOREIGN KEY, UNIQUE, INDEX, CHECK
    when not inline with a column).
    """
    skip_prefixes = (
        "primary key",
        "foreign key",
        "unique",
        "constraint",
        "index",
        "key ",
    )
    fields: list[str] = []
    for raw in body.splitlines():
        line = raw.strip().rstrip(",")
        if not line:
            continue
        if not _SQL_FIELD_LINE_RE.match(line):
            continue
        lowered = line.lower()
        if any(lowered.startswith(p) for p in skip_prefixes):
            continue
        fields.append(line)
        if len(fields) >= 50:
            break
    return fields


def _sql_relationships(body: str) -> list[str]:
    """Return referenced table names from FOREIGN KEY ... REFERENCES clauses."""
    return sorted({m.group(1) for m in _SQL_FK_RE.finditer(body)})
