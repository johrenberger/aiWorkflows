from __future__ import annotations

from pathlib import Path

from ..models import Config, FileRecord


def _matches_any(path: str, patterns: list[str]) -> bool:
    p = Path(path)
    return any(p.match(pattern) for pattern in patterns)


def classify_file(path: str, config: Config) -> tuple[bool, str]:
    p = Path(path)
    lower = p.name.lower()
    if any(token in lower for token in config.generated_file_patterns) or any(token in p.as_posix().lower() for token in config.generated_file_patterns):
        return False, "generated-file-pattern"
    if _matches_any(path, config.excluded_globs):
        return False, "excluded-glob"
    if lower.endswith((".min.js", ".min.css")):
        return False, "minified-asset"
    if not _matches_any(path, config.eligible_source_globs):
        return False, "not-source-eligible"
    if config.exclude_simple_dto and any(token in lower for token in ("dto", "record")):
        return False, "simple-dto-disabled"
    if config.exclude_migrations and any(token in lower for token in ("migration", "migrate", "schema")):
        return False, "migration-disabled"
    if config.exclude_config and any(token in lower for token in ("config", "settings", "application.properties", "application.yml")):
        return False, "config-disabled"
    return True, ""


def file_is_test(path: str) -> bool:
    lower = path.lower().replace("\\", "/")
    return "/test/" in lower or lower.endswith((".test.js", ".spec.js", ".test.ts", ".spec.ts", ".test.jsx", ".spec.jsx", ".test.tsx", ".spec.tsx", "test.py")) or "/tests/" in lower or lower.startswith("tests/")


def record_from_path(path: Path, repo_root: Path, language: str, module: str, size: int) -> FileRecord:
    return FileRecord(
        path=str(path.relative_to(repo_root)).replace("\\", "/"),
        language=language,
        module=module,
        size=size,
        is_test=file_is_test(str(path.relative_to(repo_root)).replace("\\", "/")),
    )
