from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from mutationctl.git.branch_plan import plan_branch
from mutationctl.git.commit_gate import execute_commit, plan_commit
from mutationctl.git.fake_adapter import FakeGitAdapter
from mutationctl.models import ChangedFile, GitStatus
from mutationctl.state.store import StateStore


def _status(files=None) -> GitStatus:
    return GitStatus("main", "abc1234", bool(files), files or [], [], ["fake git status"])


def test_given_allow_commit_false_when_commit_planned_then_commit_blocked_by_default(tmp_path: Path) -> None:
    store = StateStore(tmp_path); store.initialize(); store.seed_complete_validation_evidence()
    plan, gate = plan_commit(store, _status([ChangedFile("tests/test_sample.py","modified",True,"test")]), False)
    assert gate.commit_allowed is False


def test_given_allow_commit_true_but_validation_fails_when_commit_planned_then_blocking_gates_recorded(tmp_path: Path) -> None:
    store = StateStore(tmp_path); store.initialize()
    plan, gate = plan_commit(store, _status(), True)
    assert gate.commit_allowed is False
    assert gate.blockers


def test_given_unexpected_production_change_when_commit_planned_then_commit_blocked(tmp_path: Path) -> None:
    store = StateStore(tmp_path); store.initialize(); store.seed_complete_validation_evidence()
    plan, gate = plan_commit(store, _status([ChangedFile("src/sample.py","modified",False,"production")]), True)
    assert gate.commit_allowed is False
    assert "src/sample.py" in plan.excluded_files


def test_given_test_only_changes_and_validation_passes_when_commit_planned_then_commit_allowed(tmp_path: Path) -> None:
    store = StateStore(tmp_path); store.initialize(); store.seed_complete_validation_evidence()
    plan, gate = plan_commit(store, _status([ChangedFile("tests/test_sample.py","modified",True,"test")]), True)
    assert plan.commit_allowed is True
    assert "Mutation evidence:" in plan.commit_message


def test_given_current_branch_main_when_branch_planned_then_safe_workflow_branch_is_proposed() -> None:
    plan = plan_branch("main", "sample-repo", "run-123", existing_branches=[])
    assert plan.proposed_branch == "mutationctl/sample-repo/run-123"
    assert plan.safe_to_create is True


def test_given_allowed_commit_plan_when_fake_git_executes_then_fake_commit_sha_is_persisted(tmp_path: Path) -> None:
    store = StateStore(tmp_path); store.initialize(); store.seed_complete_validation_evidence()
    plan, _ = plan_commit(store, _status([ChangedFile("tests/test_sample.py","modified",True,"test")]), True)
    result = execute_commit(plan, FakeGitAdapter(), store)
    assert result.commit_created is True
    assert store.list_commit_execution_results()[0].commit_sha.startswith("fake-")


def test_given_commit_plan_cli_when_run_then_commit_remains_blocked_by_default(project_root: Path, tmp_path: Path) -> None:
    StateStore(tmp_path).initialize()
    completed = subprocess.run([sys.executable,"-m","mutationctl","commit-plan","--workspace",str(tmp_path)],cwd=project_root,capture_output=True,text=True,check=False)
    assert completed.returncode == 0
    assert '"commit_allowed": false' in completed.stdout
