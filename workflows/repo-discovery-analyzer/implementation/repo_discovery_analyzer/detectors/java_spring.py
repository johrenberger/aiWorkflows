from __future__ import annotations

import re
from pathlib import Path

from ..io_utils import DEFAULT_MAX_SUMMARY_ITEMS, safe_read_text, short_snippet
from ..model import FileRecord


RE_CLASS = re.compile(r"\bclass\s+([A-Za-z0-9_]+)")
RE_REQUEST = re.compile(r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping)\s*(?:\(([^)]*)\))?')
RE_PATH = re.compile(r'(?:value|path)\s*=\s*"(.*?)"')
RE_METHOD = re.compile(r'Method\.(GET|POST|PUT|DELETE|PATCH)')


def detect_java_spring_routes(repo_path: Path, owner: str, repo: str, commit: str, records: list[FileRecord]) -> dict:
    routes: list[dict] = []
    schema: list[dict] = []
    route_total = 0
    entity_total = 0
    for record in records:
        if not record.path.endswith(".java") or record.skipped:
            continue
        text, _ = safe_read_text(repo_path / record.path)
        if not text:
            continue
        lines = text.splitlines()
        pending_annotations: list[str] = []
        class_name = None
        for idx, line in enumerate(lines, start=1):
            if line.strip().startswith("@"):
                pending_annotations.append(line.strip())
                continue
            class_match = RE_CLASS.search(line)
            if class_match:
                class_name = class_match.group(1)
            for annotation in pending_annotations:
                if any(tag in annotation for tag in ("GetMapping", "PostMapping", "PutMapping", "DeleteMapping", "PatchMapping", "RequestMapping")):
                    method, path = _java_route(annotation)
                    if method and path:
                        route_total += 1
                        if len(routes) < DEFAULT_MAX_SUMMARY_ITEMS:
                            routes.append({
                                "method": method,
                                "path": path,
                                "source_file": record.path,
                                "github_url": record.github_url,
                                "handler": class_name,
                                "framework": "Spring MVC",
                                "confidence": "high",
                            })
                if "@Entity" in annotation:
                    entity_name = class_name or Path(record.path).stem
                    fields = _java_fields(lines)
                    entity_total += 1
                    if len(schema) < DEFAULT_MAX_SUMMARY_ITEMS:
                        schema.append({
                            "name": entity_name,
                            "source_file": record.path,
                            "github_url": record.github_url,
                            "fields": fields,
                            "relationships": _java_relationships(text),
                            "migration_source_type": "jpa-entity",
                            "confidence": "high",
                        })
            pending_annotations = []

    routes = sorted(routes, key=lambda x: (x["source_file"], x["method"], x["path"]))
    schema = sorted(schema, key=lambda x: (x["source_file"], x["name"]))
    return {
        "routes": routes,
        "routes_total": route_total,
        "routes_truncated": route_total > len(routes),
        "entities": schema,
        "entities_total": entity_total,
        "entities_truncated": entity_total > len(schema),
    }


def _java_route(annotation: str) -> tuple[str | None, str | None]:
    method = None
    if "GetMapping" in annotation:
        method = "GET"
    elif "PostMapping" in annotation:
        method = "POST"
    elif "PutMapping" in annotation:
        method = "PUT"
    elif "DeleteMapping" in annotation:
        method = "DELETE"
    elif "PatchMapping" in annotation:
        method = "PATCH"
    elif "RequestMapping" in annotation:
        m = RE_METHOD.search(annotation)
        if m:
            method = m.group(1)
        else:
            method = "GET"
    m = RE_PATH.search(annotation)
    if m:
        return method, m.group(1)
    string_match = re.search(r'"([^"]+)"', annotation)
    return method, string_match.group(1) if string_match else None


def _java_fields(lines: list[str]) -> list[str]:
    fields = []
    for line in lines:
        if re.search(r"\b(private|public|protected)\b.+;", line):
            fields.append(short_snippet(line, 80) or line.strip())
    return fields[:25]


def _java_relationships(text: str) -> list[str]:
    rels = []
    for needle in ("@OneToMany", "@ManyToOne", "@ManyToMany", "@OneToOne", "@JoinColumn"):
        if needle in text:
            rels.append(needle)
    return rels
