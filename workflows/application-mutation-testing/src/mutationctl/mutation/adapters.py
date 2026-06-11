from __future__ import annotations

from pathlib import Path

from mutationctl.models import Blocker, MutationRunResult, MutationTarget
from mutationctl.mutation.mutmut import MutmutAdapter
from mutationctl.mutation.pit import PitAdapter
from mutationctl.mutation.stryker import StrykerAdapter

ADAPTERS = {
    "mutmut": MutmutAdapter,
    "stryker": StrykerAdapter,
    "pit": PitAdapter,
}


def execute_baseline(target: MutationTarget, tool_name, working_directory: str | Path, runner, store):
    if not tool_name or tool_name not in ADAPTERS:
        store.record_blocker(
            Blocker("MUTATION_TOOL_NOT_FOUND", "BLOCKED", "No supported mutation tool was detected", target.source_file)
        )
        return None

    mutation_command = ADAPTERS[tool_name]().build_command(target, working_directory)
    command_result = runner.run(
        mutation_command.command,
        cwd=mutation_command.working_directory,
        timeout=mutation_command.timeout_seconds,
    )
    command_result.command = mutation_command.command
    store.record_command(command_result)
    status = "BLOCKED" if command_result.timed_out else command_result.status
    result = MutationRunResult(
        tool_name,
        target.source_file,
        mutation_command.command,
        command_result.exit_code,
        status,
        command_result.duration_seconds,
        command_result.stdout_path,
        command_result.stderr_path,
        [],
        command_result.timed_out,
    )
    store.record_mutation_run(result)
    if command_result.timed_out:
        store.record_blocker(
            Blocker("MUTATION_TIMEOUT", "BLOCKED", "Mutation baseline timed out", target.source_file)
        )
    return result
