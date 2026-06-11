from __future__ import annotations

import hashlib
import os
from pathlib import Path, PurePosixPath

from ..models import Config, FileRecord
from .eligibility import classify_file, file_is_test
from .module_detector import detect_language_and_module


SOURCE_SUFFIXES = {".java", ".js", ".jsx", ".ts", ".tsx", ".py", ".groovy"}


def _matches_glob(path: str, pattern: str) -> bool:
    posix = PurePosixPath(path)
    return posix.match(pattern) or PurePosixPath(f"./{path}").match(pattern)


def _matches_excluded(path: str, patterns: list[str], *, directory: bool = False) -> bool:
    candidates = [path]
    if directory:
        candidates.append(f"{path}/__placeholder__")
    for pattern in patterns:
        token = pattern.replace("**/", "").replace("/**", "").strip("/")
        if token and token in path.split("/"):
            return True
        if any(_matches_glob(candidate, pattern) for candidate in candidates):
            return True
    return False


def _is_binary(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            chunk = handle.read(4096)
    except OSError:
        return True
    return b"\0" in chunk


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8192), b""):
            h.update(block)
    return h.hexdigest()


def _prune_directories(repo_root: Path, current_root: Path, dir_names: list[str], config: Config) -> list[dict[str, str]]:
    exclusions: list[dict[str, str]] = []
    keep: list[str] = []
    for name in sorted(dir_names):
        child = current_root / name
        rel = str(child.relative_to(repo_root)).replace("\\", "/")
        if _matches_excluded(rel, config.excluded_globs, directory=True):
            exclusions.append({"path": rel, "reason": "excluded-glob", "rule": "config.excluded_globs", "adapter": ""})
            continue
        keep.append(name)
    dir_names[:] = keep
    return exclusions


def inventory_repo(repo_root: str | Path, config: Config, module: str | None = None) -> tuple[list[FileRecord], list[dict[str, str]]]:
    repo_root = Path(repo_root)
    files: list[FileRecord] = []
    exclusions: list[dict[str, str]] = []
    module_scope = (module or "").replace("\\", "/").strip("/")
    for root_str, dir_names, file_names in os.walk(repo_root):
        root = Path(root_str)
        exclusions.extend(_prune_directories(repo_root, root, dir_names, config))
        for file_name in sorted(file_names):
            path = root / file_name
            rel = str(path.relative_to(repo_root)).replace("\\", "/")
            if module_scope and not rel.startswith(f"{module_scope}/") and f"/{module_scope}/" not in rel:
                if not rel.startswith(("tests/", "test/", "src/test/", "src/integrationTest/")):
                    continue
            if _matches_excluded(rel, config.excluded_globs):
                exclusions.append({"path": rel, "reason": "excluded-glob", "rule": "config.excluded_globs", "adapter": ""})
                continue
            size = path.stat().st_size
            if size > config.max_source_file_chars:
                exclusions.append({"path": rel, "reason": "large-file", "rule": "max_source_file_chars", "adapter": ""})
                continue
            if _is_binary(path):
                exclusions.append({"path": rel, "reason": "binary-file", "rule": "binary-detection", "adapter": ""})
                continue
            language, detected_module, evidence = detect_language_and_module(repo_root, path)
            eligible, reason = classify_file(rel, config)
            record = FileRecord(
                path=rel,
                language=language,
                module=detected_module,
                size=size,
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
    exclusions = sorted({(item["path"], item["reason"], item["rule"], item.get("adapter", "")) for item in exclusions})
    normalized_exclusions = [
        {"path": path, "reason": reason, "rule": rule, "adapter": adapter}
        for path, reason, rule, adapter in exclusions
    ]
    return files, normalized_exclusions
