from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from mutationctl.command_runner import FakeCommandRunner
from mutationctl.ledger.renderer import render_ledger
from mutationctl.models import CommandResult
from mutationctl.state.store import StateStore
from mutationctl.validation.mutation_recheck import plan_recheck, run_recheck


def _data(project_root: Path, name: str) -> dict:
    return json.loads((project_root / "tests" / "fixtures" / "recheck" / name).read_text(encoding="utf-8"))


def test_given_baseline_result_when_recheck_planned_then_same_tool_and_scope_are_used(project_root: Path) -> None:
    plan = plan_recheck(_data(project_root, "baseline_mutation_result.json"))
    assert plan.tool_name == "mutmut"
    assert plan.target_file == "src/sample.py"
    assert plan.recheck_command == ["mutmut", "run", "--paths-to-mutate", "src/sample.py"]


def test_given_improved_recheck_result_when_recorded_then_before_after_and_delta_are_persisted(project_root: Path, tmp_path: Path) -> None:
    store = StateStore(tmp_path); store.initialize()
    baseline = _data(project_root, "baseline_mutation_result.json"); store.record_recheck_baseline(baseline)
    result = run_recheck(store, FakeCommandRunner([CommandResult([],0,1.0,"PASS")]), _data(project_root, "improved_recheck_result.json"))
    assert result.score_delta == 20.0
    assert store.list_mutation_recheck_results()[0].survived_after == 1


def test_given_unchanged_recheck_result_when_recorded_then_remaining_survivors_are_persisted(project_root: Path, tmp_path: Path) -> None:
    store = StateStore(tmp_path); store.initialize(); store.record_recheck_baseline(_data(project_root, "baseline_mutation_result.json"))
    result = run_recheck(store, FakeCommandRunner([CommandResult([],0,1.0,"PASS")]), _data(project_root, "unchanged_recheck_result.json"))
    assert result.status == "PARTIAL"
    assert len(store.list_remaining_survivors()) == 2


def test_given_recheck_timeout_when_run_then_timeout_blocker_or_failure_recorded(project_root: Path, tmp_path: Path) -> None:
    store = StateStore(tmp_path); store.initialize(); store.record_recheck_baseline(_data(project_root, "baseline_mutation_result.json"))
    result = run_recheck(store, FakeCommandRunner([CommandResult([],None,30.0,"FAIL",timed_out=True)]), _data(project_root, "recheck_timeout_result.json"))
    assert result.status == "BLOCKED"
    assert store.list_blockers()[-1].code == "MUTATION_RECHECK_TIMEOUT"


def test_given_missing_baseline_when_recheck_requested_then_no_command_runs_and_blocker_recorded(tmp_path: Path) -> None:
    store = StateStore(tmp_path); store.initialize(); runner = FakeCommandRunner()
    result = run_recheck(store, runner, {})
    assert result is None
    assert runner.commands == []


def test_given_remaining_survivors_when_ledger_rendered_then_survivors_are_included(project_root: Path, tmp_path: Path) -> None:
    store = StateStore(tmp_path); store.initialize(); store.record_recheck_baseline(_data(project_root, "baseline_mutation_result.json"))
    run_recheck(store, FakeCommandRunner([CommandResult([],0,1.0,"PASS")]), _data(project_root, "improved_recheck_result.json"))
    ledger = render_ledger(store).read_text(encoding="utf-8")
    assert "## Mutation Recheck" in ledger
    assert "mutmut-2: src/sample.py:7 string_replacement" in ledger


def test_given_recheck_cli_when_fake_fixture_used_then_improvement_is_reported(project_root: Path, tmp_path: Path) -> None:
    store = StateStore(tmp_path); store.initialize(); store.record_recheck_baseline(_data(project_root, "baseline_mutation_result.json"))
    fixture = project_root / "tests" / "fixtures" / "recheck" / "improved_recheck_result.json"
    completed = subprocess.run([sys.executable,"-m","mutationctl","recheck","--workspace",str(tmp_path),"--fake","--fixture",str(fixture)], cwd=project_root, capture_output=True, text=True, check=False)
    assert completed.returncode == 0
    assert '"score_delta": 20.0' in completed.stdout


def test_given_validation_exists_when_recheck_completes_then_recheck_gate_is_refreshed(project_root: Path, tmp_path: Path) -> None:
    from mutationctl.validation.gates import evaluate_validation_gates
    store = StateStore(tmp_path); store.initialize()
    store.record_recheck_baseline(_data(project_root, "baseline_mutation_result.json"))
    evaluate_validation_gates(store)
    run_recheck(store, FakeCommandRunner([CommandResult([],0,1.0,"PASS")]), _data(project_root, "improved_recheck_result.json"))
    gate = next(item for item in store.get_latest_validation_summary().gates if item.gate_id == "MT-VAL-9")
    assert gate.status == "PASS"
