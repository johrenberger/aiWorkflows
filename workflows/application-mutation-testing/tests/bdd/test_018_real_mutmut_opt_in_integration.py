from __future__ import annotations

import os
from pathlib import Path

import pytest

from mutationctl.models import MutationTarget, RealToolPolicy
from mutationctl.workflow.real_tool_policy import evaluate_real_mutmut_policy


def _target():
    return MutationTarget("src/sample.py","python",80,"PASS","selected",80,50,100,True)


def test_given_real_tools_disabled_when_mutmut_requested_then_execution_blocked(tmp_path: Path) -> None:
    decision=evaluate_real_mutmut_policy(RealToolPolicy(),tmp_path,[_target()],executable_found=True,dirty=False)
    assert decision.allowed is False


def test_given_real_tools_enabled_but_mutmut_missing_when_policy_checked_then_execution_blocked(tmp_path: Path) -> None:
    policy=RealToolPolicy(allow_real_tools=True,allow_mutmut=True)
    decision=evaluate_real_mutmut_policy(policy,tmp_path,[_target()],executable_found=False,dirty=False)
    assert "mutmut executable was not found" in decision.reasons


def test_given_dirty_tree_and_clean_required_when_policy_checked_then_execution_blocked(tmp_path: Path) -> None:
    policy=RealToolPolicy(allow_real_tools=True,allow_mutmut=True)
    decision=evaluate_real_mutmut_policy(policy,tmp_path,[_target()],executable_found=True,dirty=True)
    assert decision.allowed is False


def test_given_real_mutmut_allowed_when_command_built_then_command_is_scoped_to_selected_target(tmp_path: Path) -> None:
    policy=RealToolPolicy(allow_real_tools=True,allow_mutmut=True)
    decision=evaluate_real_mutmut_policy(policy,tmp_path,[_target()],executable_found=True,dirty=False)
    assert decision.allowed is True
    assert "src.sample*" in " ".join(decision.command)
    assert "Scoped selected target: src/sample.py" in decision.reasons


def test_given_real_mutmut_cli_without_flags_when_requested_then_blocked_by_default(project_root: Path, tmp_path: Path) -> None:
    import subprocess, sys
    (tmp_path/"sample.py").write_text("def f():\n    return 1\n",encoding="utf-8")
    completed=subprocess.run([sys.executable,"-m","mutationctl","run-baseline","--repo-path",str(tmp_path),"--target-file","sample.py"],cwd=project_root,capture_output=True,text=True,check=False)
    assert completed.returncode == 0
    assert '"status": "BLOCKED"' in completed.stdout


@pytest.mark.skipif(os.getenv("MUTATIONCTL_RUN_REAL_MUTMUT_TESTS") != "1", reason="real mutmut integration is opt-in")
def test_given_env_var_missing_when_real_mutmut_tests_collected_then_real_execution_is_skipped():
    assert os.getenv("MUTATIONCTL_RUN_REAL_MUTMUT_TESTS") == "1"
