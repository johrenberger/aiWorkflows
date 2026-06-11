from __future__ import annotations

from pathlib import Path

from mutationctl.command_runner import FakeCommandRunner
from mutationctl.models import CommandResult, MutationTarget
from mutationctl.mutation.adapters import execute_baseline
from mutationctl.mutation.mutmut import MutmutAdapter
from mutationctl.state.store import StateStore


def _target() -> MutationTarget:
    return MutationTarget(
        source_file="src/app/service.py",
        language="python",
        score=80.0,
        eligibility_status="PASS",
        rationale="selected",
        coverage_readiness=80.0,
        complexity_score=60.0,
        runtime_feasibility=100.0,
        selected=True,
    )


def test_given_mutmut_target_when_command_built_then_scoped_mutmut_command_is_returned(tmp_path: Path) -> None:
    command = MutmutAdapter().build_command(_target(), tmp_path)
    assert command.command == ["mutmut", "run", "--paths-to-mutate", "src/app/service.py"]


def test_given_fake_successful_runner_when_baseline_runs_then_command_result_is_persisted(tmp_path: Path) -> None:
    store = StateStore(tmp_path)
    store.initialize()
    runner = FakeCommandRunner(
        [CommandResult(["mutmut"], 0, 1.25, "PASS", "stdout.log", "stderr.log")]
    )
    result = execute_baseline(_target(), "mutmut", tmp_path, runner, store)
    assert result.status == "PASS"
    assert store.list_mutation_results()[0].runtime_seconds == 1.25
    assert store.list_commands()[0].stdout_path == "stdout.log"


def test_given_fake_timeout_when_baseline_runs_then_timeout_is_recorded_as_blocker_or_failure(tmp_path: Path) -> None:
    store = StateStore(tmp_path)
    store.initialize()
    runner = FakeCommandRunner(
        [CommandResult(["mutmut"], None, 30.0, "FAIL", timed_out=True)]
    )
    result = execute_baseline(_target(), "mutmut", tmp_path, runner, store)
    assert result.status == "BLOCKED"
    assert store.list_blockers()[0].code == "MUTATION_TIMEOUT"


def test_given_missing_tool_when_baseline_requested_then_no_command_runs_and_blocker_recorded(tmp_path: Path) -> None:
    store = StateStore(tmp_path)
    store.initialize()
    runner = FakeCommandRunner()
    result = execute_baseline(_target(), None, tmp_path, runner, store)
    assert result is None
    assert runner.commands == []
    assert store.list_blockers()[0].code == "MUTATION_TOOL_NOT_FOUND"
