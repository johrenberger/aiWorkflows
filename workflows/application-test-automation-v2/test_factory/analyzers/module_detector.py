from __future__ import annotations

from pathlib import Path


def detect_language_and_module(repo_root: Path, path: Path) -> tuple[str, str, dict[str, str]]:
    rel = path.relative_to(repo_root).as_posix()
    suffix = path.suffix.lower()
    evidence: dict[str, str] = {}
    language = "unknown"
    if suffix == ".java" or "pom.xml" in rel:
        language = "java"
        evidence["suffix"] = suffix
    elif suffix in {".js", ".jsx", ".ts", ".tsx"} or "package.json" in rel or "jest" in rel or "vitest" in rel:
        language = "javascript"
        evidence["suffix"] = suffix
    elif suffix == ".py" or "pyproject.toml" in rel or "requirements.txt" in rel or "setup.py" in rel:
        language = "python"
        evidence["suffix"] = suffix
    elif suffix == ".groovy" or "build.gradle" in rel:
        language = "groovy"
        evidence["suffix"] = suffix
        if "spec" in path.stem.lower() or "test" in path.stem.lower():
            evidence["framework"] = "spock"
    module = _derive_module(repo_root, path, language)
    return language, module, evidence


def _derive_module(repo_root: Path, path: Path, language: str) -> str:
    rel = path.relative_to(repo_root).as_posix()
    parts = rel.split("/")
    if language == "java":
        for anchor in ("src/main/java/", "src/test/java/"):
            if anchor in rel:
                tail = rel.split(anchor, 1)[1]
                module = "/".join(tail.split("/")[:-1])
                return module or "root"
    if language == "groovy":
        for anchor in ("src/main/groovy/", "src/test/groovy/"):
            if anchor in rel:
                tail = rel.split(anchor, 1)[1]
                module = "/".join(tail.split("/")[:-1])
                return module or "root"
    if language == "javascript":
        for anchor in ("src/", "lib/", "app/", "packages/"):
            if rel.startswith(anchor):
                return "/".join(parts[:2]) if len(parts) > 1 and parts[0] == "packages" else "/".join(parts[:-1]) or "root"
    if language == "python":
        for anchor in ("src/", "package/", "packages/", "app/", "tests/"):
            if rel.startswith(anchor):
                return "/".join(parts[:-1]) or "root"
    return "/".join(parts[:-1]) or "root"

