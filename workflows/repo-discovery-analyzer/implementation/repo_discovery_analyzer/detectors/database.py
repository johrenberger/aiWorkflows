from __future__ import annotations

import re
from pathlib import Path

from ..io_utils import safe_read_text
from ..model import FileRecord


def detect_database_schema(repo_path: Path, owner: str, repo: str, commit: str, records: list[FileRecord]) -> dict:
    entities: list[dict] = []
    for record in records:
        if record.skipped:
            continue
        text, _ = safe_read_text(repo_path / record.path)
        if not text:
            continue
        if record.path.endswith(".java") and "@Entity" in text:
            entities.append(
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
            entities.append(
                {
                    "name": _sql_table_name(text, record.path),
                    "source_file": record.path,
                    "github_url": record.github_url,
                    "fields": _sql_fields(text),
                    "relationships": [],
                    "migration_source_type": "sql",
                    "confidence": "high",
                }
            )
        if record.path.endswith("schema.prisma"):
            entities.append(
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
    return {"entities": entities}


def _java_entity_name(text: str, path: str) -> str:
    m = re.search(r"class\s+([A-Za-z0-9_]+)", text)
    return m.group(1) if m else Path(path).stem


def _java_fields(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if re.search(r"\b(private|public|protected)\b.+;", line)][:40]


def _java_relationships(text: str) -> list[str]:
    return [needle for needle in ("@OneToMany", "@ManyToOne", "@ManyToMany", "@OneToOne") if needle in text]


def _sql_table_name(text: str, path: str) -> str:
    m = re.search(r"create\s+table\s+`?\"?([A-Za-z0-9_]+)`?\"?", text, re.I)
    return m.group(1) if m else Path(path).stem


def _sql_fields(text: str) -> list[str]:
    fields = []
    for line in text.splitlines():
        if re.match(r"\s*[A-Za-z0-9_]+\s+", line):
            fields.append(line.strip().rstrip(","))
    return fields[:50]

