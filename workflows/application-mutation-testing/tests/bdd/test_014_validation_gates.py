from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from mutationctl.models import Blocker, SurvivorClassification
from mutationctl.state.store import StateStore
from mutationctl.validation.gates import evaluate_validation_gates


def test_given_complete_evidence_when_validation_runs_then_required_gates_pass(tmp_path: Path) -> None:
    store = StateStore(tmp_path); store.initialize(); store.seed_complete_validation_evidence()
    summary = evaluate_validation_gates(store, allow_commit=False)
    assert summary.fail_count == 0
    assert summary.required_gates_passed is True


def test_given_missing_tool_without_blocker_when_validation_runs_then_tool_gate_fails(tmp_path: Path) -> None:
    store = StateStore(tmp_path); store.initialize()
    summary = evaluate_validation_gates(store)
    gate = next(item for item in summary.gates if item.gate_id == "MT-VAL-3")
    assert gate.status == "FAIL"


def test_given_missing_tool_with_blocker_when_validation_runs_then_tool_gate_blocked(tmp_path: Path) -> None:
    store = StateStore(tmp_path); store.initialize()
    store.record_blocker(Blocker("MUTATION_TOOL_NOT_FOUND", "BLOCKED", "Install disabled", "pyproject.toml"))
    summary = evaluate_validation_gates(store)
    gate = next(item for item in summary.gates if item.gate_id == "MT-VAL-3")
    assert gate.status == "BLOCKED"


def test_given_survivor_classification_without_evidence_when_validation_runs_then_survivor_gate_fails(tmp_path: Path) -> None:
    store = StateStore(tmp_path); store.initialize()
    store.record_survivor_classification(SurvivorClassification("c1","m1","src/a.py",1,"op","Missing assertion","medium",[],"add assertion",False,False,"deterministic"))
    summary = evaluate_validation_gates(store)
    gate = next(item for item in summary.gates if item.gate_id == "MT-VAL-6")
    assert gate.status == "FAIL"


def test_given_allow_commit_false_when_validation_runs_then_commit_blocked_by_default(tmp_path: Path) -> None:
    store = StateStore(tmp_path); store.initialize()
    summary = evaluate_validation_gates(store, allow_commit=False)
    gate = next(item for item in summary.gates if item.gate_id == "MT-VAL-11")
    assert gate.status == "PASS"
    assert summary.commit_allowed is False


def test_given_allow_commit_true_but_gates_fail_when_validation_runs_then_commit_not_allowed(tmp_path: Path) -> None:
    store = StateStore(tmp_path); store.initialize()
    summary = evaluate_validation_gates(store, allow_commit=True)
    assert summary.commit_allowed is False
    assert "MT-VAL-12" in summary.blocking_gate_ids


def test_given_safe_but_unapplied_patch_when_validation_runs_then_hardening_gate_does_not_pass(tmp_path: Path) -> None:
    from mutationctl.models import PatchSafetyResult
    store = StateStore(tmp_path); store.initialize()
    store.record_patch_safety_result(PatchSafetyResult("p1","PASS",True,[],[],[],False,["tests/test_sample.py"]))
    summary = evaluate_validation_gates(store)
    gate = next(item for item in summary.gates if item.gate_id == "MT-VAL-7")
    assert gate.status == "NOT_RUN"


def test_given_validate_cli_when_run_then_summary_is_printed(project_root: Path, tmp_path: Path) -> None:
    StateStore(tmp_path).initialize()
    completed = subprocess.run([sys.executable, "-m", "mutationctl", "validate", "--workspace", str(tmp_path)], cwd=project_root, capture_output=True, text=True, check=False)
    assert completed.returncode == 0
    assert "commit_allowed" in completed.stdout
