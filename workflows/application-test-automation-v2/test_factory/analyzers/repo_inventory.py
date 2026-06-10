from __future__ import annotations

import hashlib
from pathlib import Path

from ..models import Config, FileRecord
from .eligibility import classify_file, file_is_test
from .module_detector import detect_language_and_module


def _is_binary(path: Path) -> bool:
    try:
        chunk = path.read_bytes()[:4096]
    except OSError:
        return True
    return b"\0" in chunk


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8192), b""):
            h.update(block)
    return h.hexdigest()


def inventory_repo(repo_root: str | Path, config: Config) -> tuple[list[FileRecord], list[dict[str, str]]]:
    repo_root = Path(repo_root)
    files: list[FileRecord] = []
    exclusions: list[dict[str, str]] = []
    for path in sorted(repo_root.rglob("*")):
        if not path.is_file():
            continue
        rel = str(path.relative_to(repo_root)).replace("\\", "/")
        if any(path.match(pattern) for pattern in config.excluded_globs):
            exclusions.append({"path": rel, "reason": "excluded-glob", "rule": "config.excluded_globs", "adapter": ""})
            continue
        if path.stat().st_size > config.max_source_file_chars and path.suffix.lower() not in {".java", ".js", ".jsx", ".ts", ".tsx", ".py"}:
            exclusions.append({"path": rel, "reason": "large-file", "rule": "max_source_file_chars", "adapter": ""})
            continue
        if _is_binary(path):
            exclusions.append({"path": rel, "reason": "binary-file", "rule": "binary-detection", "adapter": ""})
            continue
        language, module, evidence = detect_language_and_module(repo_root, path)
        eligible, reason = classify_file(rel, config)
        record = FileRecord(
            path=rel,
            language=language,
            module=module,
            size=path.stat().st_size,
            sha256=_hash_file(path),
            is_test=file_is_test(rel),
            is_generated=any(token in path.name.lower() for token in config.generated_file_patterns),
            is_excluded=not eligible,
            exclusion_reason=reason,
            evidence=evidence,
        )
        files.append(record)
        if not eligible:
            exclusions.append({"path": rel, "reason": reason, "rule": "eligibility", "adapter": language})
    files.sort(key=lambda r: (r.module, r.path))
    exclusions.sort(key=lambda item: item["path"])
    return files, exclusions

