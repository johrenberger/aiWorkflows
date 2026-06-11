from __future__ import annotations

from mutationctl.models import FocusedTestCommand, FocusedTestResult


def run_focused_tests(command: FocusedTestCommand, runner, store=None) -> FocusedTestResult:
    result = runner.run(command.command, cwd=command.working_directory, timeout=command.timeout_seconds)
    focused = FocusedTestResult(
        command.command, result.exit_code, "BLOCKED" if result.timed_out else result.status,
        result.duration_seconds, result.stdout_path, result.stderr_path,
        [" ".join(command.command), result.stdout_path or "stdout unavailable", result.stderr_path or "stderr unavailable"],
    )
    if store:
        store.record_focused_test_result(focused)
    return focused
