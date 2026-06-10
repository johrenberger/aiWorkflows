#!/usr/bin/env python3
"""synthesize_evidence.py — Convert repo-discovery-analyzer JSON outputs into
the 16 app-dev-discovery evidence markdown files.

This is the deterministic backbone of the workflow. It reads the analyzer's
JSON outputs and renders each one into the matching evidence template. The
agent's role is then narrowed to narrative synthesis, Mermaid diagrams,
risk interpretation, contradiction explanation, and confidence scoring.

Mapping (analyzer JSON → evidence file):

  analysis_manifest.json     → 00-run-metadata.md
  repo_inventory.json        → 01-file-inventory.md
  project_structure.json     → 04-structure-evidence.md
  tech_stack.json            → 03-stack-evidence.md
  entry_points.json          → 04-structure-evidence.md (merged)
  routes.json                → 09-api-evidence.md
  db_schema.json             → 07-data-evidence.md
  dependencies.json          → 08-dependencies-integrations-evidence.md
  integrations.json          → 08 (append integrations section)
  tests.json                 → 10-testing-evidence.md
  error_logging.json         → 11-error-logging-evidence.md
  security_signals.json      → 12-security-evidence.md
  build_deploy.json          → 13-build-deploy-evidence.md
  hygiene_findings.json      → 14-risk-hygiene-evidence.md
  contradiction_candidates.json → 15-contradiction-detection.md

The 02-documentation-evidence.md and 16-final-validation.md files are NOT
generated here — both need narrative judgment from the agent.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# Caps for inline tables in evidence files. Each is tuned so a typical
# (medium-sized) repo produces a file under 5 KB; very large monorepos
# truncate to MAX_INLINE rows and emit a sidecar-style summary at the
# bottom pointing to the full list in the analyzer JSON.
MAX_INLINE = 50           # generic (01 file inventory)
MAX_INLINE_ROUTES = 50    # 09 api
MAX_INLINE_ENTITIES = 30  # 07 db schema
MAX_INLINE_DEPS = 50      # 08 deps + integrations
MAX_INLINE_DIRS = 15      # 04 notable directories
MAX_INLINE_HYGIENE = 30   # 14 hygiene findings

# Top-level layout entries to always exclude (synthesizer runtime / git
# state, not part of the project).
_TOP_LEVEL_EXCLUDE = {".openclaw", ".git", ".run-state", ".idea", "node_modules"}

# Java reserved keywords that should never be confused with class names.
_JAVA_KEYWORDS = frozenset({
    "abstract", "and", "as", "assert", "boolean", "break", "byte", "case",
    "catch", "char", "class", "const", "continue", "default", "do", "double",
    "else", "enum", "extends", "final", "finally", "float", "for", "goto",
    "if", "implements", "import", "instanceof", "int", "interface", "is",
    "long", "native", "new", "not", "null", "or", "package", "private",
    "protected", "public", "return", "short", "static", "strictfp", "super",
    "switch", "synchronized", "this", "throw", "throws", "transient", "try",
    "void", "volatile", "while", "with",
})


def load_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"WARN: {path} is not valid JSON: {e}", file=sys.stderr)
        return None


def fmt_url(url: str | None) -> str:
    if not url:
        return "_(no evidence URL)_"
    return f"[`{url.rsplit('/', 1)[-1]}`]({url})" if "/" in url else url


def render_00_run_metadata(analyzer_out: Path, owner: str, repo: str, commit: str) -> str:
    manifest = load_json(analyzer_out / "analysis_manifest.json") or {}
    actual_commit = manifest.get("commit") or commit
    source_prefix = manifest.get("source_url_prefix") or f"https://github.com/{owner}/{repo}/blob/{actual_commit}/"
    elapsed = manifest.get("elapsed_ms", 0)
    return f"""# Phase 0 — Run Metadata

- **Repository:** {owner}/{repo}
- **Remote URL:** https://github.com/{owner}/{repo}
- **Default branch:** _(see git checkout)_
- **Current commit:** `{actual_commit}`
- **Commit-pinned URL prefix:** {source_prefix}
- **Run date:** _(see `run.sh` invocation)_
- **Workspace:** _(see `run.sh` invocation)_
- **Workflow:** app-dev-discovery
- **Analyzer:** {manifest.get('tool_name', 'repo-discovery-analyzer')} v{manifest.get('tool_version', '?')}
- **Analyzer elapsed:** {elapsed} ms
- **Skipped files:** {len(manifest.get('skipped_files') or [])}
- **Warnings:** {len(manifest.get('warnings') or [])}

> The metadata above is produced deterministically by the repo-discovery-analyzer
> workflow. The agent fills in workspace/date fields when this file is included
> in the final commit.
"""


def render_01_file_inventory(analyzer_out: Path) -> str:
    inv = load_json(analyzer_out / "repo_inventory.json") or {"files": []}
    files = inv.get("files", [])
    total = len(files)
    reviewed = sum(1 for f in files if f.get("reviewed_by_analyzer"))
    skipped = sum(1 for f in files if f.get("skipped"))

    # For the on-disk evidence, only include the top N files by line count
    # (the most informative for onboarding). The full inventory lives in
    # `repo_inventory.json` next to the analyzer output for the agent to
    # reference if needed.
    MAX_INLINE = 50
    reviewed_files = [f for f in files if not f.get("skipped")]
    reviewed_files.sort(key=lambda f: f.get("line_count") or 0, reverse=True)
    inline_files = reviewed_files[:MAX_INLINE]
    omitted = len(reviewed_files) - len(inline_files)

    rows = []
    for f in inline_files:
        url = f.get("github_url", "")
        rows.append(
            f"| `{f.get('path', '?')}` | {f.get('extension') or '—'} "
            f"| {f.get('language_guess') or '—'} | {f.get('role_guess') or '—'} "
            f"| {f.get('line_count', '—')} | [link]({url}) |"
        )

    # Skipped group (also capped)
    skipped_files = [f for f in files if f.get("skipped")]
    skipped_files.sort(key=lambda f: f.get("path", ""))
    skipped_inline = skipped_files[:MAX_INLINE]
    skipped_omitted = len(skipped_files) - len(skipped_inline)
    skipped_rows = [
        f"| `{f.get('path', '?')}` | {f.get('skip_reason') or '—'} |"
        for f in skipped_inline
    ]

    out = [
        "# Phase 1 — File Inventory",
        "",
        "## Summary",
        f"- Total files: **{total}**",
        f"- Reviewed by analyzer: **{reviewed}**",
        f"- Excluded: **{skipped}**",
        "",
        f"## Inventory (top {len(inline_files)} reviewed files by line count)"
        + (f" — {omitted} more in `repo_inventory.json`" if omitted else ""),
        "",
        "| Path | Ext | Language | Role | Lines | Evidence |",
        "| --- | --- | --- | --- | ---: | --- |",
        *rows,
        "",
    ]
    if skipped_rows:
        out += [
            f"## Excluded Files (first {len(skipped_inline)})"
            + (f" — {skipped_omitted} more in `repo_inventory.json`" if skipped_omitted else ""),
            "",
            "| Path | Reason |",
            "| --- | --- |",
            *skipped_rows,
            "",
        ]
    out += [
        "## Excluded Categories (standard)",
        "- `.git/`",
        "- `node_modules/`",
        "- Build artifacts",
        "- Coverage outputs",
        "- Binary/media (unless doc/deploy relevant)",
        "- Lockfile internals (beyond dep/version extraction)",
        "",
    ]
    return "\n".join(out)


def render_03_stack_evidence(analyzer_out: Path) -> str:
    stack = load_json(analyzer_out / "tech_stack.json") or {"technologies": []}
    techs = stack.get("technologies", [])

    # Group by category, keep stable ordering
    by_cat: dict[str, list[dict[str, Any]]] = {}
    for t in techs:
        by_cat.setdefault(t.get("category", "other"), []).append(t)

    cat_order = [
        "language", "framework", "backend-framework", "frontend-framework",
        "package-manager", "build-tool", "test-framework", "lint-format",
        "database", "cache", "search", "message-broker", "cloud",
        "container", "infrastructure", "ci", "platform", "testing",
    ]
    seen = set()
    ordered_cats = [c for c in cat_order if c in by_cat] + [
        c for c in sorted(by_cat) if c not in cat_order
    ]

    out = [
        "# Phase 3 — Technology Stack Detection",
        "",
        "> Generated deterministically from `tech_stack.json`. The agent may extend this",
        "> with a one-line narrative per technology if it adds value, but the rows",
        "> themselves are machine-verified and commit-pinned.",
        "",
        "| Category | Technology | Version | Confidence | Evidence |",
        "| --- | --- | --- | --- | --- |",
    ]
    for cat in ordered_cats:
        for t in by_cat[cat]:
            url = (t.get("evidence_urls") or [None])[0]
            out.append(
                f"| {cat} | {t.get('technology', '?')} "
                f"| {t.get('version') or '—'} "
                f"| {t.get('confidence', '?')} | {fmt_url(url)} |"
            )
            seen.add(t.get("technology"))

    out += [
        "",
        "## Architecture Style",
        "_To be filled by the agent based on the technologies above. Suggested_",
        "_starting point: monolith / modular monolith / microservices / serverless /_",
        "_library / CLI / etc., with 1-2 lines of evidence from the inventory._",
        "",
    ]
    return "\n".join(out)


def render_04_structure_evidence(analyzer_out: Path) -> str:
    struct = load_json(analyzer_out / "project_structure.json") or {}
    entries = load_json(analyzer_out / "entry_points.json") or {}
    inv = load_json(analyzer_out / "repo_inventory.json") or {"files": []}

    out = ["# Phase 4 — Project Structure & Entry Point Mapping", ""]
    out += ["## Top-level Layout", ""]
    # Top-level layout: filter out synthesizer runtime / git state. The
    # `.openclaw` directory is created by the synthesizer at run-time; the
    # user shouldn't see it in the project structure. Directories from
    # the analyzer's project_structure.json end with '/', files do not.
    for entry in struct.get("top_level_entries", []):
        name = entry.rstrip("/")
        if name in _TOP_LEVEL_EXCLUDE:
            continue
        if entry.endswith("/"):
            out.append(f"- `{entry}`")
        else:
            out.append(f"- `{entry}`")
    out.append("")

    out += ["## Notable Directories", ""]
    out += ["| Directory | Files |", "| --- | ---: |"]
    notable = struct.get("notable_directories", [])
    for d in notable[:MAX_INLINE_DIRS]:
        out.append(f"| `{d.get('path', '?')}` | {d.get('file_count', 0)} |")
    if len(notable) > MAX_INLINE_DIRS:
        out.append("")
        out.append(
            f"_(Showing top {MAX_INLINE_DIRS} of {len(notable)} notable "
            f"directories. Full list: `{analyzer_out / 'project_structure.json'}`.)_"
        )
    out.append("")

    out += ["## Detected Entry Points", ""]
    out += ["| Type | Framework | Handler | Path | Confidence | Evidence |",
            "| --- | --- | --- | --- | --- | --- |"]
    eps = entries.get("entry_points", [])
    for ep in eps[:MAX_INLINE]:
        out.append(
            f"| {ep.get('type', '?')} | {ep.get('framework') or '—'} "
            f"| {ep.get('handler') or '—'} | `{ep.get('path', '?')}` "
            f"| {ep.get('confidence', '?')} | {fmt_url(ep.get('github_url'))} |"
        )
    if len(eps) > MAX_INLINE:
        out.append("")
        out.append(
            f"_(Showing first {MAX_INLINE} of {len(eps)} entry points. "
            f"Full list: `{analyzer_out / 'entry_points.json'}`.)_"
        )
    out.append("")

    out += ["## Recommended Reading Order", ""]
    out += ["_(Generated by analyzer, in priority order. The agent may override based on_",
            "_its assessment of the codebase.)_", ""]
    for i, p in enumerate(struct.get("reading_order", [])[:MAX_INLINE], 1):
        out.append(f"{i}. `{p}`")
    out.append("")

    out += [
        "## Bootstrap / Configuration Files",
        "",
        "| File | Type | Evidence |",
        "| --- | --- | --- |",
    ]
    # Pull out config files from inventory. The heuristic: prefer config
    # files that are actual configuration (xml, yml, yaml, properties, json,
    # toml, ini, env) or Spring Boot main classes / Spring config classes.
    # Avoid matching arbitrary Java source files that happen to contain
    # "Manager" or "Application" in the name.
    config_extensions = {
        ".xml", ".yml", ".yaml", ".properties", ".json", ".toml",
        ".ini", ".env", ".conf", ".cfg", ".gradle", ".kts",
    }
    config_filename_exact = {
        "main.py", "app.py", "server.py", "wsgi.py", "asgi.py", "manage.py",
        "settings.py", "settings.gradle", "settings.gradle.kts", "pom.xml",
        "build.gradle", "build.gradle.kts", "package.json", "tsconfig.json",
        "application.yml", "application.yaml", "application.properties",
    }
    spring_main_classes = {
        "Application.java", "Bootstrap.java", "Main.java",
    }
    config_rows = 0
    config_total = 0
    for f in inv.get("files", []):
        if f.get("skipped"):
            continue
        path = f.get("path", "")
        if not path:
            continue
        p = Path(path)
        ext = p.suffix.lower()
        stem = p.stem
        full_name = p.name
        is_config = (
            ext in config_extensions
            or full_name in config_filename_exact
            or (ext == ".java" and (p.parent.match("**/*config*") or p.parent.name in (
                "config", "configuration", "autoconfig", "boot",
            )))
            or (ext == ".java" and full_name in spring_main_classes)
        )
        if is_config:
            config_total += 1
            if config_rows < MAX_INLINE_DIRS:
                out.append(
                    f"| `{path}` | {f.get('role_guess') or '—'} "
                    f"| {fmt_url(f.get('github_url'))} |"
                )
                config_rows += 1
    if config_total > MAX_INLINE_DIRS:
        out.append("")
        out.append(
            f"_(Showing first {MAX_INLINE_DIRS} of {config_total} config/bootstrap "
            f"files. Full list: `{analyzer_out / 'repo_inventory.json'}`.)_"
        )
    out.append("")
    return "\n".join(out)


def render_05_components_evidence(analyzer_out: Path) -> str:
    """Skeleton only — the agent is expected to fill in component narratives
    because 'why does this component matter' is genuinely a judgment call."""
    entries = load_json(analyzer_out / "entry_points.json") or {}
    routes = load_json(analyzer_out / "routes.json") or {}
    n_routes = len(routes.get("routes", []))
    eps = entries.get("entry_points", [])
    eps_table = "\n".join(
        f"| {ep.get('type', '?')} | {ep.get('framework') or '—'} "
        f"| `{ep.get('path', '?')}` | {fmt_url(ep.get('github_url'))} |"
        for ep in eps[:MAX_INLINE]
    )
    extra = ""
    if len(eps) > MAX_INLINE:
        extra = (
            f"\n_(Showing first {MAX_INLINE} of {len(eps)} entry points. "
            f"Full list: `{analyzer_out / 'entry_points.json'}`.)_"
        )
    return f"""# Phase 5 — Key Component Analysis

> This file is the agent's narrative layer over the deterministic component
> inventory below. The table is machine-generated; the prose is human-generated.

## Component Inventory (deterministic)

| Type | Framework | Path | Evidence |
| --- | --- | --- | --- |
{eps_table}
{extra}

## Component Narratives (agent-generated)

The agent should write 1-3 short paragraphs per important component describing: name, responsibility, dependencies, downstream consumers, and why it matters. The inventory above provides a starting list; the agent may add additional components found in source (currently {n_routes} API route(s) are detected across the codebase).

<!-- AGENT_FILL_REQUIRED -->
"""


def render_06_flows_evidence(analyzer_out: Path) -> str:
    """Skeleton — flow tracing is LLM judgment, but the agent gets a list of
    candidate flows based on detected routes/entry points."""
    routes = load_json(analyzer_out / "routes.json") or {}
    entries = load_json(analyzer_out / "entry_points.json") or {}
    n_routes = len(routes.get("routes", []))
    n_eps = len(entries.get("entry_points", []))
    inline_routes = routes.get("routes", [])[:MAX_INLINE_ROUTES]
    triggers_table = "\n".join(
        f"| {r.get('method', '?')} | `{r.get('path', '?')}` "
        f"| {r.get('framework') or '—'} | {fmt_url(r.get('github_url'))} |"
        for r in inline_routes
    )
    extra = ""
    if n_routes > MAX_INLINE_ROUTES:
        extra = (
            f"\n_(Showing first {MAX_INLINE_ROUTES} of {n_routes} routes. "
            f"Full list: `{analyzer_out / 'routes.json'}`.)_"
        )
    return f"""# Phase 6 — Execution & Data Flow Analysis

> This file is the agent's narrative layer. The agent traces critical flows
> end-to-end (auth, request handling, CRUD, jobs, message processing, file
> upload/download, external API interaction) and writes 1-3 sentences per flow.
> The analyzer detected {n_routes} API route(s) and {n_eps} entry point(s) —
> these are the natural starting points for the trace.

## Detected Triggers (deterministic)

| Method | Path | Framework | Source |
| --- | --- | --- | --- |
{triggers_table}
{extra}

## Flow Narratives (agent-generated)

_For each critical flow, document: trigger, entry point, major steps, data read/write behavior, error handling, persistence target, external services involved._

<!-- AGENT_FILL_REQUIRED -->
"""


def render_07_data_evidence(analyzer_out: Path) -> str:
    schema = load_json(analyzer_out / "db_schema.json") or {"entities": []}
    raw_entities = schema.get("entities", [])
    if not raw_entities:
        return """# Phase 7 — Database & Schema Analysis

> **No clear persistence layer was found** in the analyzer scan. Evidence: empty
> `db_schema.json` from the analyzer. If the agent finds additional evidence
> (e.g. SQL files, ORM config not detected by the analyzer), it should append
> to this file before validation.
"""

    # Filter: drop entities whose name is a Java/English keyword — these are
    # false positives from the analyzer's `class\s+IDENT` regex matching the
    # word "class" inside comments and string literals (e.g. "class names and
    # mapping files"). We also drop names containing whitespace or punctuation.
    entities = [
        e for e in raw_entities
        if e.get("name", "").lower() not in _JAVA_KEYWORDS
        and re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", e.get("name", "")) is not None
    ]
    filtered = len(raw_entities) - len(entities)

    # Dedup by (name, source_type) — prefer the entry with the most fields
    # and relationships (i.e. the most informative variant).
    seen: dict[tuple[str, str], dict] = {}
    for e in entities:
        key = (e.get("name", ""), e.get("migration_source_type", ""))
        existing = seen.get(key)
        if existing is None:
            seen[key] = e
        else:
            existing_score = (
                len(existing.get("fields") or [])
                + len(existing.get("relationships") or [])
            )
            new_score = (
                len(e.get("fields") or [])
                + len(e.get("relationships") or [])
            )
            if new_score > existing_score:
                seen[key] = e
    deduped = list(seen.values())

    out = [
        "# Phase 7 — Database & Schema Analysis",
        "",
        "> Generated deterministically from `db_schema.json`. The agent may",
        "> extend each entity with field-level commentary or relationship",
        "> analysis if it adds value.",
        "",
        "## Summary",
        "",
    ]
    # Summary table: count entities by source_type. Useful when the inline
    # table is truncated.
    from collections import Counter
    type_counts = Counter(e.get("migration_source_type") or "—" for e in deduped)
    for t, n in type_counts.most_common():
        out.append(f"- **{t}**: {n} entities")
    if filtered:
        out.append(
            f"- _(filtered {filtered} keyword/garbage entity name(s) "
            f"from analyzer — see {analyzer_out / 'db_schema.json'} for raw)_"
        )
    out += ["", "## Entities / Tables / Collections", ""]
    out += ["| Name | Source Type | Fields | Relationships | Confidence | Evidence |",
            "| --- | --- | ---: | ---: | --- | --- |"]
    for e in deduped[:MAX_INLINE_ENTITIES]:
        out.append(
            f"| {e.get('name', '?')} | {e.get('migration_source_type') or '—'} "
            f"| {len(e.get('fields') or [])} | {len(e.get('relationships') or [])} "
            f"| {e.get('confidence', '?')} | {fmt_url(e.get('github_url'))} |"
        )
    if len(deduped) > MAX_INLINE_ENTITIES:
        out.append("")
        out.append(
            f"_(Showing first {MAX_INLINE_ENTITIES} of {len(deduped)} entities. "
            f"Full list: `{analyzer_out / 'db_schema.json'}`.)_"
        )

    out += [
        "",
        "## Entity Details (top 5 by field count)",
        "",
    ]
    for e in sorted(
        deduped, key=lambda x: -len(x.get("fields") or [])
    )[:5]:
        out.append(f"### {e.get('name', '?')}")
        out.append(f"- **Source file:** `{e.get('source_file', '?')}`")
        out.append(f"- **Source type:** {e.get('migration_source_type') or '—'}")
        if e.get("fields"):
            out.append("- **Fields:**")
            for fld in e["fields"][:20]:
                out.append(f"  - `{fld}`")
        if e.get("relationships"):
            out.append(f"- **Relationships:** {len(e['relationships'])}")
        out.append("")
    return "\n".join(out)

    out += [
        "## Critical Indexes / Constraints",
        "",
        "_Agent should add 1-2 lines per index/constraint discovered in source,_",
        "_or state explicitly that no indexes were detected._",
        "",
    ]
    return "\n".join(out)


def render_08_dependencies_integrations(analyzer_out: Path) -> str:
    deps = load_json(analyzer_out / "dependencies.json") or {"dependencies": []}
    integrations = load_json(analyzer_out / "integrations.json") or {"integrations": []}
    dep_list = deps.get("dependencies", [])
    int_list = integrations.get("integrations", [])

    # Dedup dependencies by (name, version, ecosystem, source_file)
    seen_d: set[tuple[str, str, str, str]] = set()
    deduped_deps = []
    for d in dep_list:
        key = (
            d.get("name", ""),
            d.get("version") or "",
            d.get("ecosystem", ""),
            d.get("source_file", ""),
        )
        if key in seen_d:
            continue
        seen_d.add(key)
        deduped_deps.append(d)

    # Dedup integrations by (category, technology)
    seen_i: set[tuple[str, str]] = set()
    deduped_int = []
    for i in int_list:
        key = (i.get("category", ""), i.get("technology", ""))
        if key in seen_i:
            continue
        seen_i.add(key)
        deduped_int.append(i)

    out = [
        "# Phase 8 — Dependencies & Integrations",
        "",
        "> Generated deterministically from `dependencies.json` and",
        "> `integrations.json`. URLs are commit-pinned by the analyzer.",
        "",
        "## Major Libraries",
        "",
        "| Library | Version | Ecosystem | Role | Evidence |",
        "| --- | --- | --- | --- | --- |",
    ]
    for d in deduped_deps[:MAX_INLINE_DEPS]:
        role = d.get("likely_role") or "—"
        out.append(
            f"| {d.get('name', '?')} | {d.get('version') or '—'} "
            f"| {d.get('ecosystem', '?')} | {role} | {fmt_url(d.get('github_url'))} |"
        )
    if len(deduped_deps) > MAX_INLINE_DEPS:
        out.append("")
        out.append(
            f"_(Showing first {MAX_INLINE_DEPS} of {len(deduped_deps)} libraries. "
            f"Full list: `{analyzer_out / 'dependencies.json'}`.)_"
        )

    out += [
        "",
        "## External Integrations",
        "",
        "| Category | Technology | Confidence | Evidence |",
        "| --- | --- | --- | --- |",
    ]
    if deduped_int:
        for i in deduped_int:
            url = (i.get("evidence_urls") or [None])[0]
            out.append(
                f"| {i.get('category', '?')} | {i.get('technology', '?')} "
                f"| {i.get('confidence', '?')} | {fmt_url(url)} |"
            )
    else:
        out += [
            "| _none_ | — | — | — |",
        ]

    out += [
        "",
        "## Auth Providers / APIs",
        "",
        "_Agent should populate from source code analysis (e.g. OAuth setup,_",
        "_API client initialization). The analyzer currently detects integrations_",
        "_via package-name matching; behavioral auth patterns require source review._",
        "",
    ]
    return "\n".join(out)


def render_09_api_evidence(analyzer_out: Path) -> str:
    routes_data = load_json(analyzer_out / "routes.json") or {"routes": []}
    routes = routes_data.get("routes", [])
    if not routes:
        return """# Phase 9 — API Surface

> **No API routes detected by the analyzer.** The agent should verify this
> matches the source — routes may exist in patterns the analyzer doesn't
> recognize (e.g. older Express versions, custom routers, GraphQL).
"""

    out = [
        "# Phase 9 — API Surface",
        "",
        "## API Style",
        "_Agent should determine: REST / GraphQL / gRPC / tRPC / mixed._",
        "",
        "## Endpoint Inventory (deterministic)",
        "",
        "| Method | Path | Framework | Handler | Confidence | Evidence |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for r in routes[:MAX_INLINE_ROUTES]:
        # Normalize: every path should start with `/`. The analyzer sometimes
        # emits parameterized paths without the leading slash (e.g. when the
        # controller annotation doesn't include one).
        path = r.get("path", "?")
        if path and not path.startswith("/") and path != "?":
            path = "/" + path
        out.append(
            f"| {r.get('method', '?')} | `{path}` "
            f"| {r.get('framework') or '—'} | {r.get('handler') or '—'} "
            f"| {r.get('confidence', '?')} | {fmt_url(r.get('github_url'))} |"
        )
    if len(routes) > MAX_INLINE_ROUTES:
        out.append("")
        out.append(
            f"_(Showing first {MAX_INLINE_ROUTES} of {len(routes)} routes. "
            f"Full list: `{analyzer_out / 'routes.json'}`.)_"
        )

    out += [
        "",
        "## Documentation Mechanism",
        "",
        "_Agent should look for OpenAPI/Swagger specs, Javadoc, docstring_",
        "_conventions, or generated docs. None detected by the analyzer._",
        "",
    ]
    return "\n".join(out)


def render_10_testing_evidence(analyzer_out: Path) -> str:
    test_data = load_json(analyzer_out / "tests.json") or {"testing": []}
    tests = test_data.get("testing", [])
    ratio = test_data.get("source_to_test_ratio", {})

    out = [
        "# Phase 10 — Testing Analysis",
        "",
        f"- **Test/source ratio:** {ratio.get('ratio', '?')} "
        f"({ratio.get('test_files', 0)} test files / {ratio.get('source_files', 0)} source files)",
        "",
        "## Detected Test Frameworks / Commands",
        "",
        "| Type | Framework/Tool | Command | Confidence | Evidence |",
        "| --- | --- | --- | --- | --- |",
    ]
    for t in tests:
        cmd = t.get("command") or "—"
        out.append(
            f"| {t.get('type', '?')} | {t.get('framework_tool') or '—'} "
            f"| `{cmd}` | {t.get('confidence', '?')} | "
            f"{fmt_url((t.get('github_urls') or [None])[0])} |"
        )

    out += [
        "",
        "## Test Gaps / Observations",
        "",
        "_Agent should note: unit/integration/E2E coverage breakdown, fixture_",
        "_patterns, mock usage, CI test execution flow, and any obvious gaps_",
        "_in the detected test suite._",
        "",
    ]
    return "\n".join(out)


def render_11_error_logging_evidence(analyzer_out: Path) -> str:
    err = load_json(analyzer_out / "error_logging.json") or {"error_logging": []}
    items = err.get("error_logging", [])

    # Dedup by (category, technology) — the analyzer emits one row per
    # evidence path which inflates the table with duplicates.
    seen: set[tuple[str, str]] = set()
    deduped = []
    for i in items:
        key = (i.get("category", ""), i.get("technology", ""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(i)

    out = [
        "# Phase 11 — Error Handling, Logging & Observability",
        "",
        "> Generated deterministically from `error_logging.json`. The agent",
        "> may extend with global exception handler / middleware analysis",
        "> that the analyzer doesn't detect.",
        "",
        "## Detected Error / Logging Tools",
        "",
        "| Category | Technology | Confidence | Evidence |",
        "| --- | --- | --- | --- |",
    ]
    if deduped:
        for i in deduped:
            out.append(
                f"| {i.get('category', '?')} | {i.get('technology', '?')} "
                f"| {i.get('confidence', '?')} | {fmt_url(i.get('github_url'))} |"
            )
    else:
        out += [
            "| _none_ | — | — | — |",
        ]

    out += [
        "",
        "## Patterns to Investigate (agent)",
        "",
        "- Global exception handling / middleware",
        "- Custom error classes",
        "- Log format and level conventions",
        "- Retry / circuit-breaker patterns",
        "- Alerting hooks",
        "",
    ]
    return "\n".join(out)


def render_12_security_evidence(analyzer_out: Path) -> str:
    sec = load_json(analyzer_out / "security_signals.json") or {"security_signals": []}
    items = sec.get("security_signals", [])

    # Dedup by (category, indicator) — same dedup logic as 11.
    seen: set[tuple[str, str]] = set()
    deduped = []
    for i in items:
        key = (i.get("category", ""), i.get("indicator") or i.get("technology", ""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(i)

    out = [
        "# Phase 12 — Security Analysis",
        "",
        "> Generated deterministically from `security_signals.json`. The agent",
        "> must extend this with auth/authorization analysis, secrets handling,",
        ">and CSRF/CORS/CSP behavior — these require source review beyond",
        ">package-name matching.",
        "",
        "## Detected Security Signals",
        "",
        "| Category | Indicator | Confidence | Evidence |",
        "| --- | --- | --- | --- |",
    ]
    if deduped:
        for i in deduped:
            indicator = i.get("indicator") or i.get("technology") or "—"
            out.append(
                f"| {i.get('category', '?')} | {indicator} "
                f"| {i.get('confidence', '?')} | {fmt_url(i.get('github_url'))} |"
            )
    else:
        out += [
            "| _none_ | — | — | — |",
        ]

    out += [
        "",
        "## Areas to Investigate (agent)",
        "",
        "- Authentication mechanism (session, JWT, OAuth)",
        "- Authorization pattern (RBAC, ACL, scope-based)",
        "- Input validation (Zod, Joi, Pydantic, etc.)",
        "- Secrets handling (env vars, vault, dotenv)",
        "- CSRF / CORS / CSP headers",
        "- Dependency risk (outdated, vulnerable)",
        "- Password / token storage",
        "- **Do not perform destructive security testing.**",
        "",
    ]
    return "\n".join(out)


def render_13_build_deploy_evidence(analyzer_out: Path) -> str:
    bd = load_json(analyzer_out / "build_deploy.json") or {"build_deploy": []}
    items = bd.get("build_deploy", [])

    out = [
        "# Phase 13 — Build, Deployment & Operations",
        "",
        "## Detected Build / Deploy Artifacts",
        "",
        "| Type | Path | Runtime | Ports | Confidence | Evidence |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    if items:
        for i in items:
            ports = ", ".join(str(p) for p in (i.get("commands_or_ports") or [])) or "—"
            out.append(
                f"| {i.get('artifact_type', '?')} | `{i.get('path', '?')}` "
                f"| {i.get('detected_runtime') or '—'} | {ports} "
                f"| {i.get('confidence', '?')} | {fmt_url(i.get('github_url'))} |"
            )
    else:
        out += [
            "| _none_ | — | — | — | — | — |",
        ]

    out += [
        "",
        "## Build Flow",
        "_Agent should describe: build commands, output artifacts, multi-stage_",
        "_builds, caching strategy._",
        "",
        "## Deployment Flow",
        "_Agent should describe: target platform (k8s/ECS/Lambda/Vercel/etc.),_",
        "_IaC tool, rollout strategy._",
        "",
        "## Environment Variables",
        "| Var | Purpose | Required | Default | Evidence |",
        "| --- | --- | --- | --- | --- |",
        "_Agent should populate from .env.example / config files._",
        "",
        "## Local Development",
        "_Agent should document: prereqs, fastest startup path, common gotchas._",
        "",
    ]
    return "\n".join(out)


def render_14_risk_hygiene(analyzer_out: Path) -> str:
    hygiene = load_json(analyzer_out / "hygiene_findings.json") or {"hygiene_findings": []}
    items = hygiene.get("hygiene_findings", [])

    # Dedup by (type, path) — the analyzer emits duplicate rows for the
    # same finding across many files.
    seen: set[tuple[str, str]] = set()
    deduped = []
    for h in items:
        key = (h.get("type", ""), h.get("path", ""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(h)

    # Aggregate by type for the summary line
    from collections import Counter
    by_type = Counter(h.get("type", "?") for h in deduped)

    # Cap inline rows; rest are summarized
    MAX_INLINE = 30
    inline = deduped[:MAX_INLINE]
    omitted = len(deduped) - len(inline)

    out = [
        "# Phase 14 — Repository Hygiene & Architecture Risk",
        "",
        "## Summary (deterministic)",
        "",
        "| Type | Count |",
        "| --- | ---: |",
    ]
    for t, c in by_type.most_common():
        out.append(f"| {t} | {c} |")

    out += [
        "",
        f"## Findings (top {len(inline)}"
        + (f" of {len(deduped)} — rest in `hygiene_findings.json`)" if omitted else ")"),
        "",
        "| Type | Path | Confidence | Impact |",
        "| --- | --- | --- | --- |",
    ]
    if inline:
        for h in inline:
            out.append(
                f"| {h.get('type', '?')} | `{h.get('path', '?')}` "
                f"| {h.get('confidence', '?')} | {h.get('impact_hint') or '—'} |"
            )
    else:
        out += [
            "| _none_ | — | — | — |",
        ]

    out += [
        "",
        "## TODO / FIXME / HACK / XXX search",
        "",
        "_Agent should run grep for these markers, count occurrences, list top_",
        "_recurring themes, and classify each finding as:_",
        "",
        "- **Confirmed Risk** (evidence of active issue)",
        "- **Probable Risk** (likely issue, needs verification)",
        "- **Observation** (informational, no action needed)",
        "",
        "Categories: Security, Testing, Performance, Reliability, Scalability,",
        "Maintainability, Operational Readiness, Documentation.",
        "",
        "<!-- AGENT_FILL_REQUIRED -->",
        "",
    ]
    return "\n".join(out)


def render_15_contradictions(analyzer_out: Path) -> str:
    contra = load_json(analyzer_out / "contradiction_candidates.json") or {"contradiction_candidates": []}
    items = contra.get("contradiction_candidates", [])

    # Dedup by summary text
    seen: set[str] = set()
    deduped = []
    for c in items:
        key = c.get("summary", "")
        if key in seen:
            continue
        seen.add(key)
        deduped.append(c)

    out = [
        "# Phase 15 — Contradiction Detection",
        "",
        "> Generated deterministically from `contradiction_candidates.json`.",
        "> Each candidate below is a cross-evidence pattern the analyzer",
        "> detected; the agent should explain interpretation and impact.",
        "",
        "## Detected Candidates",
        "",
    ]
    if deduped:
        for i, c in enumerate(deduped, 1):
            out += [
                f"### {i}. {c.get('summary', '?')}",
                "",
                f"- **Confidence:** {c.get('confidence', '?')}",
                f"- **Evidence A:** {c.get('evidence_a', '—')}",
                f"- **Evidence B:** {c.get('evidence_b', '—')}",
                f"- **Impact hint:** {c.get('impact_hint', '—')}",
                f"- **Needs AI interpretation:** {c.get('needs_ai_interpretation', False)}",
                "",
                "_Agent should add: likely interpretation, recommended follow-up._",
                "",
            ]
    else:
        out += [
            "**No automated contradictions detected.** The agent should perform a manual",
            "cross-check between: documentation, source code, config, CI/CD, Docker,",
            "infrastructure, and tests. Look for: README vs code, Dockerfile vs CI,",
            "docs vs implemented routes, declared ports vs exposed ports.",
            "",
        ]

    out += [
        "## Areas to Cross-Check (agent)",
        "",
        "- README claims vs actual stack",
        "- CI Node/Python/Java version vs Dockerfile",
        "- Documentation auth claims vs implementation",
        "- Setup docs commands vs package.json scripts",
        "- Deployment manifests vs runtime ports",
        "- API docs vs implemented routes",
        "",
        "<!-- AGENT_FILL_REQUIRED -->",
        "",
    ]
    return "\n".join(out)


# Skeleton files (LLM-only — generated by agent)
# These contain a clearly-greppable `<!-- AGENT_FILL_REQUIRED -->` marker that
# the validate.sh script uses to detect unfilled narrative sections.
RENDER_SKELETON_02 = """# Phase 2 — Documentation & Instruction Review

> The analyzer does not extract narrative documentation content. The agent
> must review README, CONTRIBUTING, docs/, runbooks, changelogs, and important
> script comments, then summarize: project overview, setup/run instructions,
> conventions, contribution process, and documentation gaps.

<!-- AGENT_FILL_REQUIRED -->
"""

RENDER_SKELETON_16 = """# Phase 16 — Final Validation

> Filled by the validate.sh script after all evidence is on disk. Lists the
> results of every validation check (PASS/FAIL) and overall status.
"""


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--analyzer-out", required=True, type=Path)
    p.add_argument("--evidence-dir", required=True, type=Path)
    p.add_argument("--owner", required=True)
    p.add_argument("--repo", required=True)
    p.add_argument("--commit", default="")
    args = p.parse_args()

    analyzer_out: Path = args.analyzer_out
    evidence_dir: Path = args.evidence_dir
    evidence_dir.mkdir(parents=True, exist_ok=True)

    # Map: evidence filename → render function
    renders = [
        ("00-run-metadata.md", lambda: render_00_run_metadata(analyzer_out, args.owner, args.repo, args.commit)),
        ("01-file-inventory.md", lambda: render_01_file_inventory(analyzer_out)),
        ("02-documentation-evidence.md", lambda: RENDER_SKELETON_02),
        ("03-stack-evidence.md", lambda: render_03_stack_evidence(analyzer_out)),
        ("04-structure-evidence.md", lambda: render_04_structure_evidence(analyzer_out)),
        ("05-components-evidence.md", lambda: render_05_components_evidence(analyzer_out)),
        ("06-flows-evidence.md", lambda: render_06_flows_evidence(analyzer_out)),
        ("07-data-evidence.md", lambda: render_07_data_evidence(analyzer_out)),
        ("08-dependencies-integrations-evidence.md", lambda: render_08_dependencies_integrations(analyzer_out)),
        ("09-api-evidence.md", lambda: render_09_api_evidence(analyzer_out)),
        ("10-testing-evidence.md", lambda: render_10_testing_evidence(analyzer_out)),
        ("11-error-logging-evidence.md", lambda: render_11_error_logging_evidence(analyzer_out)),
        ("12-security-evidence.md", lambda: render_12_security_evidence(analyzer_out)),
        ("13-build-deploy-evidence.md", lambda: render_13_build_deploy_evidence(analyzer_out)),
        ("14-risk-hygiene-evidence.md", lambda: render_14_risk_hygiene(analyzer_out)),
        ("15-contradiction-detection.md", lambda: render_15_contradictions(analyzer_out)),
    ]

    for filename, fn in renders:
        out_path = evidence_dir / filename
        out_path.write_text(fn(), encoding="utf-8")
        size = out_path.stat().st_size
        print(f"  {filename:50s} {size:6d} bytes")

    return 0


if __name__ == "__main__":
    sys.exit(main())
