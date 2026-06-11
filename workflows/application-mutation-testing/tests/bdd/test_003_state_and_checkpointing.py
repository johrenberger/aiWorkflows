from __future__ import annotations

import sqlite3
from pathlib import Path

from mutationctl.config import load_workflow_config
from mutationctl.models import Blocker, CommandResult, RepoMetadata
from mutationctl.state.store import StateStore


def test_given_new_workspace_when_state_initialized_then_sqlite_and_directories_exist(tmp_path: Path) -> None:
    store = StateStore(tmp_path)
    store.initialize()

    state_dir = tmp_path / ".mutation-workflow"
    assert (state_dir / "state.sqlite").is_file()
    assert (state_dir / "run.json").is_file()
    assert (state_dir / "commands.jsonl").is_file()
    assert (state_dir / "reports").is_dir()
    assert (state_dir / "survivor-packets").is_dir()
    assert (state_dir / "llm-decisions").is_dir()
    assert (state_dir / "patches").is_dir()
    assert (state_dir / "TODO_mutation-testing.md").is_file()

    with sqlite3.connect(state_dir / "state.sqlite") as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }

    for required_table in [
        "runs",
        "repo_metadata",
        "commands",
        "tool_detection",
        "coverage_summaries",
        "targets",
        "mutation_results",
        "surviving_mutants",
        "survivor_classifications",
        "survivor_packets",
        "llm_requests",
        "llm_responses",
        "llm_validation_results",
        "patch_proposals",
        "patch_safety_results",
        "patch_apply_results",
        "patch_revert_results",
        "weakening_findings",
        "focused_test_results",
        "validation_gate_results",
        "validation_summaries",
        "mutation_recheck_plans",
        "mutation_recheck_results",
        "remaining_survivors",
        "git_status",
        "branch_plans",
        "commit_plans",
        "commit_gate_results",
        "commit_execution_results",
        "workflow_run_results",
        "final_summaries",
        "real_tool_policies",
        "real_tool_decisions",
        "real_tool_results",
        "validation_results",
        "ledger_tasks",
        "blockers",
        "commits",
    ]:
        assert required_table in tables


def test_given_run_metadata_when_saved_then_it_can_be_read_back(tmp_path: Path) -> None:
    store = StateStore(tmp_path)
    store.initialize()
    config = load_workflow_config({"repo": "https://github.com/example/project"})
    repo_metadata = RepoMetadata(
        repo_path=str(tmp_path),
        repo_url="https://github.com/example/project",
        branch="main",
        commit_sha="abc1234",
        is_dirty=False,
        captured_at="2026-06-10T12:00:00+00:00",
    )

    record = store.create_run(config, repo_metadata)
    fetched = store.get_run(record.run_id)

    assert fetched is not None
    assert fetched.run_id == record.run_id
    assert fetched.repo_url == "https://github.com/example/project"


def test_given_command_result_when_recorded_then_command_history_contains_it(tmp_path: Path) -> None:
    store = StateStore(tmp_path)
    store.initialize()
    result = CommandResult(
        command=["python", "-m", "pytest"],
        exit_code=0,
        duration_seconds=1.25,
        status="PASS",
        stdout_path="stdout.log",
        stderr_path="stderr.log",
    )

    store.record_command(result)
    history = store.list_commands()

    assert len(history) == 1
    assert history[0].command == ["python", "-m", "pytest"]
    assert history[0].stdout_path == "stdout.log"


def test_given_blocker_when_recorded_then_blocker_is_persisted_with_evidence(tmp_path: Path) -> None:
    store = StateStore(tmp_path)
    store.initialize()
    blocker = Blocker(
        code="INVALID_REPO",
        status="BLOCKED",
        reason="Repository URL must target GitHub",
        evidence="https://example.com/not-github/project",
    )

    store.record_blocker(blocker)
    blockers = store.list_blockers()

    assert len(blockers) == 1
    assert blockers[0].reason == blocker.reason
    assert blockers[0].evidence == blocker.evidence
