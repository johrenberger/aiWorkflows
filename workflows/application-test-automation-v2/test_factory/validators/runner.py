from __future__ import annotations

import json
import re
import subprocess
from dataclasses import asdict
from pathlib import Path

from ..models import CommandSpec, ValidationRunRecord
from ..storage import Storage


DISALLOWED_TEST_PATTERNS = [
    re.compile(r"\b(?:it|test)\.only\s*\("),
    re.compile(r"\b(?:describe)\.only\s*\("),
    re.compile(r"\bxtest\s*\("),
    re.compile(r"\bxit\s*\("),
    re.compile(r"\btodo\s*\("),
    re.compile(r"@Disabled\b"),
]


def run_command(command: CommandSpec, artifact_dir: str | Path, timeout_seconds: int, work_item_id: str, phase: str) -> ValidationRunRecord:
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / f"{work_item_id}-{phase}.json"
    try:
        completed = subprocess.run(
            command.command,
            cwd=command.cwd,
            env={**command.env} if command.env else None,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            shell=False,
        )
        record = ValidationRunRecord(
            work_item_id=work_item_id,
            command=command.render(),
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            timeout_seconds=timeout_seconds,
            artifact_path=str(artifact_path),
            phase=phase,
        )
    except subprocess.TimeoutExpired as exc:
        record = ValidationRunRecord(
            work_item_id=work_item_id,
            command=command.render(),
            exit_code=124,
            stdout=(exc.stdout or "") if isinstance(exc.stdout, str) else "",
            stderr=(exc.stderr or "") if isinstance(exc.stderr, str) else "timeout",
            timeout_seconds=timeout_seconds,
            artifact_path=str(artifact_path),
            phase=phase,
        )
    artifact_path.write_text(json.dumps(asdict(record), indent=2), encoding="utf-8")
    return record


def run_targeted_validation(storage: Storage, work_item_id: str, command: CommandSpec, artifact_dir: str | Path, timeout_seconds: int) -> ValidationRunRecord:
    record = run_command(command, artifact_dir, timeout_seconds, work_item_id, "targeted")
    storage.insert_validation_run(record)
    return record


def run_module_validation(storage: Storage, work_item_id: str, command: CommandSpec, artifact_dir: str | Path, timeout_seconds: int) -> ValidationRunRecord:
    record = run_command(command, artifact_dir, timeout_seconds, work_item_id, "module")
    storage.insert_validation_run(record)
    return record


def find_disallowed_test_markers(repo_root: str | Path, candidate_files: list[str]) -> list[str]:
    repo_root = Path(repo_root)
    violations: list[str] = []
    for relative in candidate_files:
        path = repo_root / relative
        if not path.exists() or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in DISALLOWED_TEST_PATTERNS:
            if pattern.search(text):
                violations.append(relative)
                break
    return sorted(set(violations))
