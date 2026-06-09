from __future__ import annotations

import json
import re
from pathlib import Path

from ..io_utils import safe_read_text
from ..model import FileRecord


def detect_dependencies(repo_path: Path, owner: str, repo: str, commit: str, records: list[FileRecord]) -> dict:
    deps: list[dict] = []
    seen: set[tuple[str, str, str]] = set()

    def add(name: str, version: str | None, ecosystem: str, dep_type: str | None, source_file: str, role: str | None = None):
        key = (name, version or "", source_file)
        if key in seen:
            return
        seen.add(key)
        deps.append(
            {
                "name": name,
                "version": version,
                "ecosystem": ecosystem,
                "dependency_type": dep_type,
                "source_file": source_file,
                "github_url": _url_for(records, source_file),
                "likely_role": role,
            }
        )

    pkg = repo_path / "package.json"
    if pkg.exists():
        try:
            data = json.loads(pkg.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        for section, dep_type in [("dependencies", "runtime"), ("devDependencies", "dev"), ("peerDependencies", "peer")]:
            for name, version in (data.get(section) or {}).items():
                add(name, version, "npm", dep_type, "package.json", _likely_role(name))

    requirements = repo_path / "requirements.txt"
    if requirements.exists():
        text, _ = safe_read_text(requirements)
        if text:
            for line in text.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                match = re.match(r"([A-Za-z0-9_.\-]+)([<>=!~].+)?", line)
                if match:
                    add(match.group(1), match.group(2), "pip", None, "requirements.txt", _likely_role(match.group(1)))

    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists():
        text, _ = safe_read_text(pyproject)
        if text:
            for name, version in _extract_toml_deps(text).items():
                add(name, version, "pip", None, "pyproject.toml", _likely_role(name))

    pom = repo_path / "pom.xml"
    if pom.exists():
        text, _ = safe_read_text(pom)
        if text:
            for group, artifact, version in re.findall(r"<groupId>([^<]+)</groupId>\s*<artifactId>([^<]+)</artifactId>\s*<version>([^<]+)</version>", text, re.S):
                add(artifact, version, "maven", None, "pom.xml", _likely_role(artifact))

    for gradle_name in ("build.gradle", "build.gradle.kts"):
        path = repo_path / gradle_name
        if path.exists():
            text, _ = safe_read_text(path)
            if text:
                # Accept both 2-part coords (group:artifact, common in
                # Spring Boot starter projects where the version is
                # managed by a plugin) and 3-part coords
                # (group:artifact:version). Capture the group and the
                # artifact, with version when present. Accept both
                # groovy form (implementation 'x:y:z') and kotlin form
                # (implementation("x:y:z")). Each unique artifact is
                # emitted as a separate dep keyed by the artifact id
                # (consistent with how Maven deps are emitted).
                for group, artifact, version in re.findall(
                    r"(?:implementation|api|testImplementation|compileOnly)\s*\(?\s*[\"']([^:\"']+):([^:\"']+)(?::([^\"']+))?[\"']",
                    text,
                ):
                    add(artifact, version or None, "gradle", None, gradle_name, _likely_role(artifact))

    go_mod = repo_path / "go.mod"
    if go_mod.exists():
        text, _ = safe_read_text(go_mod)
        if text:
            # go.mod lines look like:
            #   require github.com/gin-gonic/gin v1.9.1
            #   require (github.com/foo v1.0; github.com/bar v2.0)
            #   github.com/baz v1.2
            # We accept a name anywhere on the line followed by whitespace
            # and "v<digits>" (the standard go.mod version prefix).
            for name, version in re.findall(r"([A-Za-z0-9][A-Za-z0-9._/\-]*)\s+v([0-9][0-9A-Za-z.\-]*)", text):
                # Skip module path declarations and go version lines.
                stripped = name.strip()
                if stripped in {"go", "module"}:
                    continue
                add(stripped, version, "go", None, "go.mod", _likely_role(stripped))

    cargo = repo_path / "Cargo.toml"
    if cargo.exists():
        text, _ = safe_read_text(cargo)
        if text:
            for name, version in re.findall(r'([A-Za-z0-9_-]+)\s*=\s*["\']([^"\']+)["\']', text):
                add(name, version, "cargo", None, "Cargo.toml", _likely_role(name))

    deps = sorted(deps, key=lambda x: (x["ecosystem"], x["name"], x["source_file"]))
    return {"dependencies": deps}


def _extract_toml_deps(text: str) -> dict[str, str | None]:
    deps: dict[str, str | None] = {}
    for section in ("[project.dependencies]", "[tool.poetry.dependencies]"):
        if section not in text:
            continue
    for line in text.splitlines():
        line = line.strip()
        m = re.match(r"([A-Za-z0-9_.\-]+)\s*=\s*['\"]([^'\"]+)['\"]", line)
        if m:
            deps[m.group(1)] = m.group(2)
        m = re.match(r"['\"]?([A-Za-z0-9_.\-]+)['\"]?\s*([<>=!~].+)?", line)
        if m and m.group(1) not in deps and line and not line.startswith("["):
            if any(op in line for op in ("=", "<", ">", "~")):
                deps[m.group(1)] = m.group(2)
    return deps


def _likely_role(name: str) -> str | None:
    lowered = name.lower()
    mapping = [
        ("spring", "backend framework"),
        ("react", "frontend framework"),
        ("next", "frontend framework"),
        ("vue", "frontend framework"),
        ("express", "backend framework"),
        ("pytest", "testing"),
        ("jest", "testing"),
        ("vitest", "testing"),
        ("cypress", "testing"),
        ("playwright", "testing"),
        ("sentry", "observability"),
        ("opentelemetry", "observability"),
        ("prometheus", "observability"),
        ("redis", "cache"),
        ("postgres", "database"),
        ("mysql", "database"),
    ]
    for needle, role in mapping:
        if needle in lowered:
            return role
    return None


def _url_for(records: list[FileRecord], source_file: str) -> str | None:
    for record in records:
        if record.path == source_file:
            return record.github_url
    return None

