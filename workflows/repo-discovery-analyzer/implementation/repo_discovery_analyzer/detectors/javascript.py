from __future__ import annotations

import re
from pathlib import Path

from ..io_utils import DEFAULT_MAX_SUMMARY_ITEMS, safe_read_text, short_snippet
from ..model import FileRecord


RE_ROUTE = re.compile(r'\b(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*([`"\'])(.+?)\2')


def detect_javascript_routes(repo_path: Path, owner: str, repo: str, commit: str, records: list[FileRecord]) -> dict:
    routes: list[dict] = []
    schema: list[dict] = []
    route_total = 0
    entity_total = 0

    for record in records:
        if record.skipped:
            continue
        text, _ = safe_read_text(repo_path / record.path)
        if not text:
            continue

        if record.path.endswith((".js", ".jsx", ".ts", ".tsx")):
            for match in RE_ROUTE.finditer(text):
                route_total += 1
                if len(routes) < DEFAULT_MAX_SUMMARY_ITEMS:
                    routes.append({
                        "method": match.group(1).upper(),
                        "path": match.group(3),
                        "source_file": record.path,
                        "github_url": record.github_url,
                        "handler": None,
                        "framework": "Express",
                        "confidence": "high",
                    })

        if "pages/api/" in record.path.replace("\\", "/") or "app/api/" in record.path.replace("\\", "/"):
            method = "GET"
            if "export async function POST" in text:
                method = "POST"
            route_total += 1
            if len(routes) < DEFAULT_MAX_SUMMARY_ITEMS:
                routes.append({
                    "method": method,
                    "path": _next_api_path(record.path),
                    "source_file": record.path,
                    "github_url": record.github_url,
                    "handler": _next_handler_name(text),
                    "framework": "Next.js API",
                    "confidence": "medium",
                })

        if record.path.endswith(("schema.prisma",)):
            entity_total += 1
            if len(schema) < DEFAULT_MAX_SUMMARY_ITEMS:
                schema.append({
                    "name": "Prisma schema",
                    "source_file": record.path,
                    "github_url": record.github_url,
                    "fields": [],
                    "relationships": [],
                    "migration_source_type": "prisma",
                    "confidence": "high",
                })

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


def _next_api_path(path: str) -> str:
    normalized = path.replace("\\", "/")
    for prefix in ("pages/api/", "app/api/"):
        if prefix in normalized:
            suffix = normalized.split(prefix, 1)[1]
            suffix = suffix.rsplit(".", 1)[0]
            suffix = suffix.replace("/route", "")
            return "/api/" + suffix.strip("/")
    return "/api"


def _next_handler_name(text: str) -> str | None:
    m = re.search(r'export\s+async\s+function\s+([A-Za-z0-9_]+)', text)
    return m.group(1) if m else None
