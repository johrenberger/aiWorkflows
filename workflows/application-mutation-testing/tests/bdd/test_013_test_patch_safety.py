from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from mutationctl.patches.apply import apply_patch_proposal
from mutationctl.patches.parser import parse_patch
from mutationctl.patches.revert import revert_patch
from mutationctl.patches.safety import validate_patch_safety


def _patch(project_root: Path, name: str):
    return parse_patch(project_root / "tests" / "fixtures" / "patches" / name)


def test_given_test_only_patch_and_test_changes_allowed_when_validated_then_patch_is_accepted(project_root: Path) -> None:
    result = validate_patch_safety(_patch(project_root, "test_only_add_assertion.patch"), allow_test_changes=True)
    assert result.accepted is True
    assert result.status == "PASS"


def test_given_test_only_patch_and_test_changes_disabled_when_validated_then_patch_is_blocked(project_root: Path) -> None:
    result = validate_patch_safety(_patch(project_root, "test_only_add_assertion.patch"))
    assert result.accepted is False
    assert "test changes are disabled" in result.reasons[0].lower()


def test_given_production_patch_when_production_fixes_disabled_then_patch_is_rejected(project_root: Path) -> None:
    result = validate_patch_safety(_patch(project_root, "production_change.patch"), allow_test_changes=True)
    assert result.accepted is False
    assert "src/sample.py" in result.rejected_files


def test_given_mixed_patch_when_validated_then_patch_is_rejected_and_human_review_required(project_root: Path) -> None:
    result = validate_patch_safety(_patch(project_root, "mixed_test_and_production.patch"), allow_test_changes=True)
    assert result.accepted is False
    assert result.requires_human_review is True


def test_given_patch_removes_assertion_when_validated_then_weakening_is_detected(project_root: Path) -> None:
    result = validate_patch_safety(_patch(project_root, "remove_assertion.patch"), allow_test_changes=True)
    assert result.accepted is False
    assert result.weakening_findings


def test_given_malformed_patch_when_validated_then_validation_fails_closed(project_root: Path) -> None:
    proposal = _patch(project_root, "malformed.patch")
    result = validate_patch_safety(proposal, allow_test_changes=True)
    assert result.status == "FAIL"
    assert result.accepted is False


def test_given_accepted_patch_when_applied_and_reverted_then_workspace_returns_to_original_state(
    project_root: Path, tmp_path: Path
) -> None:
    source = project_root / "tests" / "fixtures" / "repos" / "python_patch_safety"
    workspace = tmp_path / "repo"
    shutil.copytree(source, workspace)
    test_file = workspace / "tests" / "test_sample.py"
    original = test_file.read_text(encoding="utf-8")
    proposal = _patch(project_root, "test_only_add_assertion.patch")
    safety = validate_patch_safety(proposal, allow_test_changes=True)
    applied = apply_patch_proposal(proposal, safety, workspace)
    assert applied.applied is True
    assert "test_is_large_returns_false_for_boundary_value" in test_file.read_text(encoding="utf-8")
    reverted = revert_patch(applied, workspace)
    assert reverted.reverted is True
    assert test_file.read_text(encoding="utf-8") == original


def test_given_patch_cli_when_test_changes_allowed_then_validation_passes(project_root: Path, tmp_path: Path) -> None:
    patch = project_root / "tests" / "fixtures" / "patches" / "test_only_add_assertion.patch"
    completed = subprocess.run(
        [sys.executable, "-m", "mutationctl", "validate-patch", "--workspace", str(tmp_path), "--patch", str(patch), "--allow-test-changes"],
        cwd=project_root, capture_output=True, text=True, check=False
    )
    assert completed.returncode == 0
    assert '"accepted": true' in completed.stdout
