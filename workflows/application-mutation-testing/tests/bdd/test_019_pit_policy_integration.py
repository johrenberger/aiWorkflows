"""Story 026: PIT mutation tool real-tool-policy evaluator.

These tests verify the safety gate for running the real PIT
mutation tool against a Java repo. They mirror the structure of
`test_018_real_mutmut_opt_in_integration.py` (the mutmut policy
tests) but for PIT.

We test the policy layer only — not PIT's actual execution. The
real-PIT end-to-end is story 027 (deferred).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from mutationctl.models import MutationTarget, RealToolPolicy
from mutationctl.workflow.real_tool_policy import evaluate_real_pit_policy


def _java_target(source_file: str = "src/main/java/com/example/Calculator.java"):
    return MutationTarget(
        source_file,
        "java",
        80,
        "PASS",
        "selected",
        80,
        50,
        100,
        True,
    )


def test_given_real_tools_disabled_when_pit_requested_then_execution_blocked(tmp_path: Path) -> None:
    decision = evaluate_real_pit_policy(
        RealToolPolicy(), tmp_path, [_java_target()], executable_found=True, dirty=False
    )
    assert decision.allowed is False
    assert decision.tool_name == "pit"


def test_given_real_tools_enabled_but_pit_missing_when_policy_checked_then_execution_blocked(
    tmp_path: Path,
) -> None:
    policy = RealToolPolicy(allow_real_tools=True, allow_pit=False)
    decision = evaluate_real_pit_policy(
        policy, tmp_path, [_java_target()], executable_found=True, dirty=False
    )
    assert decision.allowed is False
    assert "PIT is not explicitly enabled" in decision.reasons


def test_given_dirty_tree_and_clean_required_when_pit_policy_checked_then_execution_blocked(
    tmp_path: Path,
) -> None:
    policy = RealToolPolicy(allow_real_tools=True, allow_pit=True)
    decision = evaluate_real_pit_policy(
        policy, tmp_path, [_java_target()], executable_found=True, dirty=True
    )
    assert decision.allowed is False
    assert "working tree is dirty" in decision.reasons


def test_given_real_pit_allowed_when_command_built_then_command_is_scoped_to_selected_target(
    tmp_path: Path,
) -> None:
    policy = RealToolPolicy(allow_real_tools=True, allow_pit=True)
    decision = evaluate_real_pit_policy(
        policy, tmp_path, [_java_target()], executable_found=True, dirty=False
    )
    assert decision.allowed is True
    cmd_str = " ".join(decision.command)
    # The command must include the PIT Maven goal:
    assert "mvn" in cmd_str
    assert "org.pitest:pitest-maven:mutationCoverage" in cmd_str
    # And it must include test-compile so PIT has the classes to mutate:
    assert "test-compile" in cmd_str
    # And it must be scoped via -DtargetClasses=<FQCN>:
    assert "-DtargetClasses=com.example.Calculator" in cmd_str
    # Reasons should mention the target we scoped to:
    assert "Scoped selected target: src/main/java/com/example/Calculator.java" in decision.reasons


def test_given_no_targets_when_pit_policy_checked_then_execution_blocked(tmp_path: Path) -> None:
    policy = RealToolPolicy(allow_real_tools=True, allow_pit=True)
    decision = evaluate_real_pit_policy(
        policy, tmp_path, [], executable_found=True, dirty=False
    )
    assert decision.allowed is False
    assert "no bounded mutation target is selected" in decision.reasons


def test_given_relative_path_when_pit_policy_checked_then_execution_blocked(tmp_path: Path) -> None:
    policy = RealToolPolicy(allow_real_tools=True, allow_pit=True)
    # Use a relative path (not absolute)
    decision = evaluate_real_pit_policy(
        policy, "relative/path", [_java_target()], executable_found=True, dirty=False
    )
    assert decision.allowed is False
    assert "repository path must be local and absolute" in decision.reasons


def test_given_mvn_missing_when_require_existing_tool_then_execution_blocked(tmp_path: Path) -> None:
    policy = RealToolPolicy(allow_real_tools=True, allow_pit=True, require_existing_tool=True)
    decision = evaluate_real_pit_policy(
        policy, tmp_path, [_java_target()], executable_found=False, dirty=False
    )
    assert decision.allowed is False
    assert "mvn executable was not found" in decision.reasons


def test_given_kotlin_target_when_policy_checked_then_target_classes_uses_kotlin_extension(
    tmp_path: Path,
) -> None:
    """The FQCN extraction handles .kt files too."""
    policy = RealToolPolicy(allow_real_tools=True, allow_pit=True)
    target = _java_target("src/main/kotlin/com/example/Adder.kt")
    decision = evaluate_real_pit_policy(
        policy, tmp_path, [target], executable_found=True, dirty=False
    )
    assert decision.allowed is True
    assert "-DtargetClasses=com.example.Adder" in " ".join(decision.command)


def test_given_target_outside_standard_layout_when_policy_checked_then_target_classes_uses_path_as_fqcn(
    tmp_path: Path,
) -> None:
    """If the path doesn't match src/main/java/ or src/main/kotlin/,
    we use the file path (with / → . and .java stripped) as the
    FQCN. E.g. `lib/SomeClass.java` → `lib.SomeClass`."""
    policy = RealToolPolicy(allow_real_tools=True, allow_pit=True)
    target = _java_target("lib/SomeClass.java")
    decision = evaluate_real_pit_policy(
        policy, tmp_path, [target], executable_found=True, dirty=False
    )
    assert decision.allowed is True
    assert "-DtargetClasses=lib.SomeClass" in " ".join(decision.command)


def test_given_too_many_targets_when_policy_checked_then_execution_blocked(tmp_path: Path) -> None:
    policy = RealToolPolicy(allow_real_tools=True, allow_pit=True)
    targets = [_java_target(f"src/main/java/com/example/Cls{i}.java") for i in range(6)]
    decision = evaluate_real_pit_policy(
        policy, tmp_path, targets, executable_found=True, dirty=False
    )
    assert decision.allowed is False
    assert "selected target count exceeds the safety cap" in decision.reasons


# --------------------------------------------------------------------------
# Story 030: clarify the chained command + test-classpath assumption
# --------------------------------------------------------------------------


def test_given_real_pit_when_command_built_then_command_does_not_chain_process_test_resources_explicitly(
    tmp_path: Path,
) -> None:
    """Story 030: the policy's Maven command should NOT explicitly
    chain process-test-resources. Maven's lifecycle runs it as part
    of test-compile. This test documents the intent and prevents a
    well-meaning future contributor from "fixing" it by adding
    the explicit phase.
    """
    policy = RealToolPolicy(allow_real_tools=True, allow_pit=True)
    decision = evaluate_real_pit_policy(
        policy, tmp_path, [_java_target()], executable_found=True, dirty=False
    )
    assert decision.allowed is True
    cmd_str = " ".join(decision.command)
    # The command should contain test-compile (the chained phase) but
    # NOT process-test-resources (it's included implicitly in
    # Maven's lifecycle, not chained explicitly).
    assert "test-compile" in cmd_str
    assert "process-test-resources" not in cmd_str, (
        "process-test-resources is part of Maven's lifecycle and runs "
        "automatically before test-compile. Don't chain it explicitly."
    )


def test_given_real_pit_when_decision_built_then_decision_documents_test_classpath_assumption(
    tmp_path: Path,
) -> None:
    """Story 030: the decision's reasons list should include a
    note about test classpath / resources. This makes the policy
    self-documenting for downstream consumers and prevents the
    "but I need process-test-resources" question from being
    re-asked every release.
    """
    policy = RealToolPolicy(allow_real_tools=True, allow_pit=True)
    decision = evaluate_real_pit_policy(
        policy, tmp_path, [_java_target()], executable_found=True, dirty=False
    )
    assert decision.allowed is True
    reasons_text = " ".join(decision.reasons)
    assert "process-test-resources" in reasons_text, (
        "Decision reasons should explain that process-test-resources "
        "is included implicitly in test-compile (Maven lifecycle)."
    )
    assert "test classpath" in reasons_text.lower() or "test resources" in reasons_text.lower(), (
        "Decision reasons should mention test classpath or test "
        "resources so consumers know what assumption is being made."
    )
