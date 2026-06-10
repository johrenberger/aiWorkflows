from __future__ import annotations

from test_factory.analyzers.risk_scorer import score_file
from test_factory.models import Config, CoverageRecord, SourceTestMapRecord
from test_factory.workitems.generator import generate_work_items
from test_factory.workitems.renderer import render_work_item_markdown


def test_work_item_generation_is_bounded(tmp_path):
    config = Config()
    coverage = CoverageRecord(path="src/foo.py", line_coverage=20.0, branch_coverage=10.0, uncovered_lines=[2], uncovered_branches=["2:0"])
    score = score_file("src/foo.py", "src", coverage, complexity=1, public_api_exposure=1)
    mapping = {"src/foo.py": SourceTestMapRecord(source_path="src/foo.py", candidate_tests=["tests/test_foo.py"], supporting_files=["pyproject.toml"], recommended_test_type="unit", conventions_summary="pytest")}
    items = generate_work_items(tmp_path, config, [coverage], [score], mapping)
    assert len(items) == 1
    rendered = render_work_item_markdown(items[0], config)
    assert "Do not modify production code" in rendered
    assert "tests/test_foo.py" in rendered


def test_work_item_ids_are_deterministic(tmp_path):
    config = Config()
    coverage = CoverageRecord(path="src/foo.py", line_coverage=20.0, branch_coverage=10.0)
    score = score_file("src/foo.py", "src", coverage, complexity=1, public_api_exposure=1)
    mapping = {"src/foo.py": SourceTestMapRecord(source_path="src/foo.py")}

    first = generate_work_items(tmp_path, config, [coverage], [score], mapping)[0]
    second = generate_work_items(tmp_path, config, [coverage], [score], mapping)[0]

    assert first.work_item_id == second.work_item_id


def test_existing_test_files_does_not_hallucinate(tmp_path):
    """Bug #7 regression: when no test files exist on disk, the workitem
    must report existing_test_files=[] and not the unfiltered candidate list."""
    config = Config()
    coverage = CoverageRecord(path="src/foo.py", line_coverage=0.0, branch_coverage=0.0)
    score = score_file("src/foo.py", "src", coverage, complexity=10, public_api_exposure=1)
    # candidate_tests=[] (filtered: nothing on disk)
    # candidate_paths=[...] (unfiltered: LLM guidance)
    mapping = {
        "src/foo.py": SourceTestMapRecord(
            source_path="src/foo.py",
            candidate_tests=[],
            candidate_paths=["tests/test_foo.py", "src/test_foo.py"],
        )
    }
    items = generate_work_items(tmp_path, config, [coverage], [score], mapping)
    assert len(items) == 1
    assert items[0].existing_test_files == [], (
        f"expected existing_test_files=[] (no tests on disk), got {items[0].existing_test_files}"
    )
    # Render and confirm the workitem does NOT show hallucinated paths
    rendered = render_work_item_markdown(items[0], config)
    assert "Existing test files" in rendered
    existing_section = rendered.split("Existing test files")[1].split("Supporting files")[0]
    assert "tests/test_foo.py" not in existing_section
    assert "src/test_foo.py" not in existing_section


def test_existing_test_files_includes_real_files(tmp_path):
    """When test files DO exist on disk, they appear in existing_test_files."""
    config = Config()
    real_test = tmp_path / "tests" / "test_foo.py"
    real_test.parent.mkdir(parents=True, exist_ok=True)
    real_test.write_text("# test stub\n")
    coverage = CoverageRecord(path="src/foo.py", line_coverage=0.0, branch_coverage=0.0)
    score = score_file("src/foo.py", "src", coverage, complexity=10, public_api_exposure=1)
    mapping = {
        "src/foo.py": SourceTestMapRecord(
            source_path="src/foo.py",
            candidate_tests=["tests/test_foo.py"],
            candidate_paths=["tests/test_foo.py", "src/test_foo.py"],
        )
    }
    items = generate_work_items(tmp_path, config, [coverage], [score], mapping)
    assert items[0].existing_test_files == ["tests/test_foo.py"]
