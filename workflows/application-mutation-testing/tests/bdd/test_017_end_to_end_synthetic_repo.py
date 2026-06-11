from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from mutationctl.state.store import StateStore
from mutationctl.workflow.orchestrator import run_synthetic_workflow


def test_given_synthetic_repo_when_report_only_run_executes_then_ledger_is_rendered_without_external_tools(project_root: Path, tmp_path: Path) -> None:
    repo = project_root/"tests/fixtures/repos/synthetic_e2e_python"
    result = run_synthetic_workflow(repo,tmp_path,"report-only",project_root/"tests/fixtures/e2e")
    assert result.status in {"PASS","PARTIAL"}
    assert Path(result.ledger_path).is_file()


def test_given_fake_survivors_when_synthetic_run_executes_then_packets_and_classifications_are_persisted(project_root: Path, tmp_path: Path) -> None:
    run_synthetic_workflow(project_root/"tests/fixtures/repos/synthetic_e2e_python",tmp_path,"report-only",project_root/"tests/fixtures/e2e")
    store=StateStore(tmp_path)
    assert len(store.list_survivor_packets()) == 2
    assert len(store.list_survivor_classifications()) == 2


def test_given_safe_patch_and_test_changes_allowed_when_fake_implementation_runs_then_patch_and_focused_test_recorded(project_root: Path, tmp_path: Path) -> None:
    result=run_synthetic_workflow(project_root/"tests/fixtures/repos/synthetic_e2e_python",tmp_path,"fake-implementation",project_root/"tests/fixtures/e2e",allow_test_changes=True)
    store=StateStore(tmp_path)
    assert store.list_patch_apply_results()[-1].applied is True
    assert store.list_focused_test_results()[-1].status == "PASS"


def test_given_improved_recheck_fixture_when_fake_implementation_runs_then_before_after_evidence_persisted(project_root: Path, tmp_path: Path) -> None:
    run_synthetic_workflow(project_root/"tests/fixtures/repos/synthetic_e2e_python",tmp_path,"fake-implementation",project_root/"tests/fixtures/e2e",allow_test_changes=True)
    assert StateStore(tmp_path).list_mutation_recheck_results()[-1].score_delta == 20.0


def test_given_completed_synthetic_run_when_validation_executes_then_gate_summary_rendered(project_root: Path, tmp_path: Path) -> None:
    result=run_synthetic_workflow(project_root/"tests/fixtures/repos/synthetic_e2e_python",tmp_path,"fake-implementation",project_root/"tests/fixtures/e2e",allow_test_changes=True)
    assert StateStore(tmp_path).get_latest_validation_summary() is not None
    assert "## Validation Gates" in Path(result.ledger_path).read_text(encoding="utf-8")


def test_given_allow_commit_false_when_synthetic_run_completes_then_commit_plan_is_blocked_by_default(project_root: Path, tmp_path: Path) -> None:
    result=run_synthetic_workflow(project_root/"tests/fixtures/repos/synthetic_e2e_python",tmp_path,"report-only",project_root/"tests/fixtures/e2e")
    assert result.commit_plan.commit_allowed is False


def test_given_synthetic_cli_when_report_only_runs_then_summary_is_created(project_root: Path, tmp_path: Path) -> None:
    repo=project_root/"tests/fixtures/repos/synthetic_e2e_python"
    completed=subprocess.run([sys.executable,"-m","mutationctl","run","--repo-path",str(repo),"--workspace",str(tmp_path),"--synthetic","--mode","report-only"],cwd=project_root,capture_output=True,text=True,check=False)
    assert completed.returncode == 0
    assert '"status":' in completed.stdout
    assert (tmp_path/".mutation-workflow/final_summary.md").is_file()
