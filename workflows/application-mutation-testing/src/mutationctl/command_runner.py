from __future__ import annotations

import subprocess
import time
from collections import deque
from pathlib import Path

from mutationctl.models import CommandResult, VALID_STATUSES


def _status_from_exit_code(exit_code: int | None, timed_out: bool = False) -> str:
    if timed_out:
        return "FAIL"
    return "PASS" if exit_code == 0 else "FAIL"


class SubprocessCommandRunner:
    def run(
        self,
        command: list[str],
        cwd: str | Path | None = None,
        timeout: float | None = None,
        stdout_path: str | None = None,
        stderr_path: str | None = None,
    ) -> CommandResult:
        start = time.perf_counter()
        timed_out = False
        try:
            completed = subprocess.run(
                command,
                cwd=str(cwd) if cwd else None,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            exit_code = completed.returncode
        except subprocess.TimeoutExpired:
            exit_code = None
            timed_out = True
        duration = time.perf_counter() - start
        status = _status_from_exit_code(exit_code, timed_out)
        if status not in VALID_STATUSES:
            status = "FAIL"
        return CommandResult(
            command=command,
            exit_code=exit_code,
            duration_seconds=duration,
            status=status,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            timed_out=timed_out,
        )


class FakeCommandRunner:
    def __init__(self, queued_results: list[CommandResult] | None = None) -> None:
        self._results = deque(queued_results or [])
        self.commands: list[list[str]] = []

    def enqueue(self, result: CommandResult) -> None:
        self._results.append(result)

    def run(
        self,
        command: list[str],
        cwd: str | Path | None = None,
        timeout: float | None = None,
        stdout_path: str | None = None,
        stderr_path: str | None = None,
    ) -> CommandResult:
        del cwd, timeout
        self.commands.append(command)
        if self._results:
            return self._results.popleft()
        return CommandResult(
            command=command,
            exit_code=0,
            duration_seconds=0.0,
            status="PASS",
            stdout_path=stdout_path,
            stderr_path=stderr_path,
        )
