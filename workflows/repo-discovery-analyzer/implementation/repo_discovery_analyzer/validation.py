from __future__ import annotations

import json
import re
from pathlib import Path


RE_COMMIT_PINNED = re.compile(r"https://github\.com/[^/\s]+/[^/\s]+/blob/[0-9a-f]{7,40}/")


def validate_outputs(
    output_dir: Path,
    required_files: list[str],
    warnings: list[str],
    repo_path: Path | None = None,
    commit: str | None = None,
) -> dict:
    checks: list[dict] = []
    failed = False
    loaded: dict[str, object] = {}
    for name in required_files:
        path = output_dir / name
        exists = path.exists()
        checks.append({"check": f"exists:{name}", "status": exists})
        failed = failed or not exists
        if exists:
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                checks.append({"check": f"json:{name}", "status": False})
                failed = True
                continue
            loaded[name] = payload
            checks.append({"check": f"json:{name}", "status": True})
            if not _urls_commit_pinned(payload):
                checks.append({"check": f"urls:{name}", "status": False})
                failed = True
            else:
                checks.append({"check": f"urls:{name}", "status": True})

    manifest = loaded.get("analysis_manifest.json")
    if isinstance(manifest, dict):
        checks.append({"check": "manifest:tool_name", "status": manifest.get("tool_name") == "repo-discovery-analyzer"})
        checks.append({"check": "manifest:tool_version", "status": bool(manifest.get("tool_version"))})
        checks.append({"check": "manifest:timestamps", "status": bool(manifest.get("start_time_utc")) and bool(manifest.get("end_time_utc"))})
        checks.append({"check": "manifest:elapsed_ms", "status": isinstance(manifest.get("elapsed_ms"), int) and manifest.get("elapsed_ms") >= 0})
        if commit is not None:
            checks.append({"check": "manifest:commit", "status": manifest.get("commit") == commit})

    inventory = loaded.get("repo_inventory.json")
    if isinstance(inventory, dict):
        files = inventory.get("files")
        has_files = isinstance(files, list) and len(files) > 0
        checks.append({"check": "inventory:has_files", "status": has_files})
        if has_files:
            all_paths_ok = True
            reviewed = 0
            for entry in files:
                if not isinstance(entry, dict):
                    all_paths_ok = False
                    continue
                rel_path = entry.get("path")
                skipped = bool(entry.get("skipped"))
                if entry.get("reviewed_by_analyzer"):
                    reviewed += 1
                if repo_path is not None and isinstance(rel_path, str):
                    exists = (repo_path / rel_path).exists()
                    if not exists and not skipped:
                        all_paths_ok = False
                    github_url = entry.get("github_url")
                    if isinstance(github_url, str) and not RE_COMMIT_PINNED.search(github_url):
                        all_paths_ok = False
            checks.append({"check": "inventory:paths", "status": all_paths_ok})
            checks.append({"check": "inventory:reviewed_files", "status": reviewed > 0})

    if warnings:
        checks.append({"check": "warnings:collected", "status": True})
    else:
        checks.append({"check": "warnings:collected", "status": True})

    status = "failed" if failed else ("passed_with_warnings" if warnings else "passed")
    if failed:
        status = "failed"
    elif warnings:
        status = "passed_with_warnings"
    return {"status": status, "checks": checks, "warnings": warnings}


def _urls_commit_pinned(payload: object) -> bool:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key.endswith("github_url") and isinstance(value, str) and value and not RE_COMMIT_PINNED.search(value):
                return False
            if not _urls_commit_pinned(value):
                return False
    elif isinstance(payload, list):
        for value in payload:
            if not _urls_commit_pinned(value):
                return False
    elif isinstance(payload, str):
        if "https://github.com/" in payload and "/blob/" in payload and not RE_COMMIT_PINNED.search(payload):
            return False
    return True
