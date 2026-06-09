from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .model import FileRecord


DEFAULT_EXCLUDES = {
    ".git",
    "node_modules",
    "dist",
    "build",
    "target",
    "coverage",
    ".next",
    ".nuxt",
    ".gradle",
    ".idea",
    ".vscode",
    "__pycache__",
    ".pytest_cache",
    "vendor",
    "bin",
    "obj",
}

TEXT_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".kt", ".kts", ".xml", ".json",
    ".yml", ".yaml", ".md", ".txt", ".toml", ".ini", ".cfg", ".conf", ".sql",
    ".gradle", ".properties", ".env", ".env.example", ".dockerfile",
}

PACKAGE_MANAGER_FILES = {
    "package-lock.json": "npm",
    "yarn.lock": "yarn",
    "pnpm-lock.yaml": "pnpm",
    "pom.xml": "maven",
    "build.gradle": "gradle",
    "build.gradle.kts": "gradle",
    "requirements.txt": "pip",
    "pyproject.toml": "python",
    "go.mod": "go",
    "Cargo.toml": "cargo",
}

RE_SECRET = re.compile(
    r"(?i)\b("
    r"api[_-]?key|secret|token|password|passwd|private[_-]?key|client[_-]?secret|"
    r"access[_-]?key|refresh[_-]?token"
    r")\b"
)

RE_URL = re.compile(r"https?://[^\s'\"<>]+")
RE_CREDENTIAL_VALUE = re.compile(r"(?i)(=|:)\s*['\"]?([A-Za-z0-9_\-+/=]{12,})['\"]?")


def safe_read_text(path: Path, max_bytes: int | None = None) -> tuple[str | None, str | None]:
    try:
        data = path.read_bytes()
    except OSError as exc:
        return None, f"unreadable: {exc.strerror or exc.__class__.__name__}"
    if max_bytes is not None and len(data) > max_bytes:
        return None, f"file exceeds max_file_bytes ({len(data)} > {max_bytes})"
    try:
        return data.decode("utf-8"), None
    except UnicodeDecodeError:
        try:
            return data.decode("utf-8", errors="replace"), None
        except Exception as exc:  # pragma: no cover - extremely defensive
            return None, f"unreadable: {exc.__class__.__name__}"


def count_lines(text: str | None) -> int | None:
    if text is None:
        return None
    if text == "":
        return 0
    return text.count("\n") + (0 if text.endswith("\n") else 1)


def normalize_path(path: Path, base: Path) -> str:
    return path.relative_to(base).as_posix()


def guess_language(path: Path) -> str:
    name = path.name.lower()
    suffix = path.suffix.lower()
    if name in {"dockerfile", "containerfile"}:
        return "Dockerfile"
    if name.endswith(".gradle.kts"):
        return "Kotlin"
    if suffix in {".ts", ".tsx"}:
        return "TypeScript"
    if suffix in {".js", ".jsx", ".mjs", ".cjs"}:
        return "JavaScript"
    if suffix == ".py":
        return "Python"
    if suffix in {".java"}:
        return "Java"
    if suffix in {".kt", ".kts"}:
        return "Kotlin"
    if suffix in {".go"}:
        return "Go"
    if suffix in {".rs"}:
        return "Rust"
    if suffix in {".xml"}:
        return "XML"
    if suffix in {".yaml", ".yml"}:
        return "YAML"
    if suffix in {".json"}:
        return "JSON"
    if suffix in {".sql"}:
        return "SQL"
    if suffix in {".toml"}:
        return "TOML"
    return "Text"


def guess_role(path: Path) -> str:
    parts = [p.lower() for p in path.parts]
    name = path.name.lower()
    if (
        any(segment in parts for segment in ("test", "tests", "spec", "specs", "__tests__"))
        or name.startswith("test_")
        or name.endswith(("_test.py", "_spec.py"))
        or ".test." in name
        or ".spec." in name
    ):
        return "test"
    if any(seg in parts for seg in ("docs", "doc", "documentation")) or name.endswith(".md"):
        return "documentation"
    if any(seg in parts for seg in ("migrations", "migration")) or name.endswith(".sql"):
        return "database"
    if name in {"dockerfile", "docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"}:
        return "deployment"
    if path.suffix.lower() in {".yaml", ".yml"} and (".github" in parts or "kubernetes" in parts or "k8s" in parts):
        return "deployment"
    if any(seg in parts for seg in ("scripts", "bin", "tools")):
        return "script"
    if name in {
        "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "pom.xml",
        "build.gradle", "build.gradle.kts", "pyproject.toml", "requirements.txt",
        "go.mod", "cargo.toml",
    }:
        return "build config"
    return "source"


def is_probably_text(path: Path) -> bool:
    lower = path.name.lower()
    if lower in {"dockerfile", "containerfile"}:
        return True
    if path.suffix.lower() in TEXT_EXTENSIONS:
        return True
    if lower.endswith(".lock"):
        return True
    return False


def redact_text(text: str) -> str:
    text = RE_URL.sub("<redacted-url>", text)
    text = RE_CREDENTIAL_VALUE.sub(lambda m: f"{m.group(1)} <redacted>", text)
    if RE_SECRET.search(text):
        return RE_SECRET.sub("<redacted-key>", text)
    return text


def short_snippet(text: str | None, limit: int = 180) -> str | None:
    if not text:
        return None
    single = " ".join(text.strip().split())
    return single[:limit]


def json_dump(path: Path, payload: Any, indent: int = 2) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=indent, sort_keys=True, ensure_ascii=False)
        fh.write("\n")


def walk_files(repo_path: Path) -> list[Path]:
    files: list[Path] = []
    for root, dirs, filenames in os.walk(repo_path):
        dirs[:] = sorted(d for d in dirs if d not in DEFAULT_EXCLUDES)
        root_path = Path(root)
        for filename in sorted(filenames):
            files.append(root_path / filename)
    return sorted(files, key=lambda p: p.relative_to(repo_path).as_posix())
