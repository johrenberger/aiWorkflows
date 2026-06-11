from __future__ import annotations

from pathlib import Path

from mutationctl.models import CoverageFileSummary
from mutationctl.state.store import StateStore
from mutationctl.targeting.selector import select_targets


def test_given_more_eligible_files_than_cap_when_targets_selected_then_cap_is_enforced(tmp_path: Path) -> None:
    for index in range(7):
        path = tmp_path / "src" / f"module_{index}.py"
        path.parent.mkdir(exist_ok=True)
        path.write_text(f"def f_{index}(x):\n    if x:\n        return x\n    return 0\n", encoding="utf-8")
    result = select_targets(tmp_path, language="python", tool_name="mutmut", max_target_files=3)
    assert len(result.selected) == 3


def test_given_generated_and_vendor_paths_when_targets_selected_then_they_are_excluded(project_root: Path) -> None:
    repo = project_root / "tests" / "fixtures" / "repos" / "python_mixed_generated_vendor"
    result = select_targets(repo, language="python", tool_name="mutmut")
    excluded_paths = {target.source_file for target in result.excluded}
    assert "generated/generated.py" in excluded_paths
    assert "vendor/vendor.py" in excluded_paths
    assert "dist/bundle.py" in excluded_paths


def test_given_files_with_different_coverage_and_complexity_when_scored_then_order_is_deterministic(
    tmp_path: Path,
) -> None:
    (tmp_path / "simple.py").write_text("def simple(x):\n    return x\n", encoding="utf-8")
    (tmp_path / "branchy.py").write_text(
        "def branchy(x):\n    if x > 10:\n        return x\n    elif x:\n        return 1\n    return 0\n",
        encoding="utf-8",
    )
    coverage = [
        CoverageFileSummary("simple.py", 70.0, None, [1], [2], "fixture", "PASS"),
        CoverageFileSummary("branchy.py", 95.0, None, [1, 2, 3, 4], [5], "fixture", "PASS"),
    ]
    result = select_targets(tmp_path, "python", "mutmut", coverage_files=coverage)
    assert result.selected[0].source_file == "branchy.py"
    assert result.selected[0].score > result.selected[1].score


def test_given_missing_coverage_when_fallback_allowed_then_targets_selected_with_rationale(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("def app(x):\n    return x + 1\n", encoding="utf-8")
    result = select_targets(tmp_path, "python", "mutmut", coverage_files=[], fallback_allowed=True)
    assert result.selected
    assert "coverage unavailable" in result.selected[0].rationale.lower()


def test_given_selection_when_store_supplied_then_selected_and_excluded_targets_persist(
    project_root: Path, tmp_path: Path
) -> None:
    repo = project_root / "tests" / "fixtures" / "repos" / "python_mixed_generated_vendor"
    store = StateStore(tmp_path)
    store.initialize()
    select_targets(repo, "python", "mutmut", max_target_files=1, store=store)
    persisted = store.list_targets()
    assert any(target.selected for target in persisted)
    assert any(target.eligibility_status == "EXCLUDED" for target in persisted)
