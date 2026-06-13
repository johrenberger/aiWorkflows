"""Story 023: v2 --module auto sentinel.

The CLI's --module flag is a string; existing values are concrete
Maven module names (e.g. "common", "admin/foo"). Story 023 adds a
new sentinel value, "auto", that means "no module filter" for
filter-style subcommands (scan, coverage, score, queue,
workitems, report, run, pr-summary).

This file pins the dispatch:

  - --module auto → module=None (no filter) for filter subcommands
  - --scope auto is an alias for --module auto
  - --module auto is rejected for branch/commit (where module is a
    target, not a filter)
  - existing --module <name> behavior is unchanged (regression)
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from test_factory.cli import (
    MODULE_AUTO,
    build_parser,
    main,
)


# ---------------------------------------------------------------------------
# Helper: build a multi-module fixture repo on disk.
# ---------------------------------------------------------------------------
@pytest.fixture
def multi_module_repo(tmp_path: Path) -> Path:
    """Create a minimal multi-module Maven repo on disk.

    Layout:
        <tmp>/pom.xml
        <tmp>/common/pom.xml + common/src/main/java/.../Foo.java
        <tmp>/admin/foo/pom.xml + admin/foo/src/main/java/.../Bar.java
    """
    # Root pom.
    (tmp_path / "pom.xml").write_text(
        '<?xml version="1.0"?>'
        '<project><modelVersion>4.0.0</modelVersion>'
        '<modules><module>common</module><module>admin/foo</module></modules>'
        '</project>',
        encoding="utf-8",
    )
    # Common module.
    (tmp_path / "common" / "pom.xml").parent.mkdir(parents=True)
    (tmp_path / "common" / "pom.xml").write_text(
        '<?xml version="1.0"?><project><modelVersion>4.0.0</modelVersion></project>',
        encoding="utf-8",
    )
    (tmp_path / "common" / "src" / "main" / "java" / "com" / "example").mkdir(parents=True)
    (tmp_path / "common" / "src" / "main" / "java" / "com" / "example" / "Foo.java").write_text(
        "package com.example;\nclass Foo {}\n", encoding="utf-8",
    )
    # Admin module.
    (tmp_path / "admin" / "foo" / "pom.xml").parent.mkdir(parents=True)
    (tmp_path / "admin" / "foo" / "pom.xml").write_text(
        '<?xml version="1.0"?><project><modelVersion>4.0.0</modelVersion></project>',
        encoding="utf-8",
    )
    (tmp_path / "admin" / "foo" / "src" / "main" / "java" / "com" / "example").mkdir(parents=True)
    (tmp_path / "admin" / "foo" / "src" / "main" / "java" / "com" / "example" / "Bar.java").write_text(
        "package com.example;\nclass Bar {}\n", encoding="utf-8",
    )
    return tmp_path


# ---------------------------------------------------------------------------
# Scenario 1: --module auto is equivalent to no filter for `scan`.
# ---------------------------------------------------------------------------
def test_module_auto_scan_includes_all_modules(multi_module_repo, tmp_path, capsys):
    """`test-factory scan --module auto` produces an inventory
    that includes files from BOTH `common/` and `admin/foo/`.
    """
    out_dir = tmp_path / "out"
    rc = main([
        "scan", "--repo", str(multi_module_repo),
        "--out", str(out_dir),
        "--module", MODULE_AUTO,
    ])
    assert rc == 0
    inv = json.loads((out_dir / "repo_inventory.json").read_text(encoding="utf-8"))
    paths = {row["path"] for row in inv}
    assert "common/src/main/java/com/example/Foo.java" in paths, (
        f"expected common module file in inventory, got: {sorted(paths)[:5]}"
    )
    assert "admin/foo/src/main/java/com/example/Bar.java" in paths, (
        f"expected admin module file in inventory, got: {sorted(paths)[:5]}"
    )


# ---------------------------------------------------------------------------
# Scenario 2: --scope auto is an alias for --module auto.
# ---------------------------------------------------------------------------
def test_scope_auto_is_alias_for_module_auto(multi_module_repo, tmp_path, capsys):
    """`test-factory scan --scope auto` produces the same
    inventory as `--module auto`. (The CLI dispatch uses
    `args.module or args.scope`; the alias only works because
    `args.module or args.scope` is replaced with
    `(_resolve_module_arg(args.module) or _resolve_module_arg(args.scope))`
    in the dispatch.)
    """
    out_dir = tmp_path / "out"
    rc = main([
        "scan", "--repo", str(multi_module_repo),
        "--out", str(out_dir),
        "--scope", MODULE_AUTO,
    ])
    assert rc == 0
    inv = json.loads((out_dir / "repo_inventory.json").read_text(encoding="utf-8"))
    paths = {row["path"] for row in inv}
    assert "common/src/main/java/com/example/Foo.java" in paths
    assert "admin/foo/src/main/java/com/example/Bar.java" in paths


# ---------------------------------------------------------------------------
# Scenario 3: --module auto keeps the existing
# "filtered to one module" behavior disabled.
# ---------------------------------------------------------------------------
def test_module_auto_disables_existing_filter(multi_module_repo, tmp_path):
    """A concrete `--module common` filters the inventory to
    common/ files. `--module auto` MUST include admin/ files
    too (the sentinel is the explicit "no filter" mode).
    """
    out_auto = tmp_path / "out-auto"
    main([
        "scan", "--repo", str(multi_module_repo),
        "--out", str(out_auto), "--module", MODULE_AUTO,
    ])
    out_filtered = tmp_path / "out-filtered"
    main([
        "scan", "--repo", str(multi_module_repo),
        "--out", str(out_filtered), "--module", "common",
    ])
    inv_auto = json.loads((out_auto / "repo_inventory.json").read_text(encoding="utf-8"))
    inv_filtered = json.loads((out_filtered / "repo_inventory.json").read_text(encoding="utf-8"))
    auto_paths = {row["path"] for row in inv_auto}
    filtered_paths = {row["path"] for row in inv_filtered}
    # --module auto includes admin/foo; --module common does not.
    assert "admin/foo/src/main/java/com/example/Bar.java" in auto_paths
    assert "admin/foo/src/main/java/com/example/Bar.java" not in filtered_paths


# ---------------------------------------------------------------------------
# Scenario 4: --module auto is rejected for branch/commit.
# ---------------------------------------------------------------------------
def test_module_auto_rejected_for_branch(multi_module_repo, tmp_path, capsys):
    """`test-factory branch --module auto` MUST error with a
    clear message (not silently treat "auto" as a module name
    and produce a confusing downstream error).
    """
    out_dir = tmp_path / "out"
    with pytest.raises(SystemExit) as exc_info:
        main([
            "branch", "--repo", str(multi_module_repo),
            "--out", str(out_dir),
            "--module", MODULE_AUTO,
        ])
    # SystemExit is the standard argparse behavior for argparse
    # errors. The error message must mention "auto" and "branch"
    # so the user understands what went wrong.
    captured = capsys.readouterr()
    combined = captured.err + captured.out
    assert MODULE_AUTO in combined or "auto" in combined.lower(), (
        f"expected error to mention 'auto', got: {combined!r}"
    )


def test_module_auto_rejected_for_commit(multi_module_repo, tmp_path, capsys):
    """`test-factory commit --module auto` MUST error with a
    clear message.
    """
    out_dir = tmp_path / "out"
    with pytest.raises(SystemExit) as exc_info:
        main([
            "commit", "--repo", str(multi_module_repo),
            "--out", str(out_dir),
            "--module", MODULE_AUTO,
        ])
    captured = capsys.readouterr()
    combined = captured.err + captured.out
    assert MODULE_AUTO in combined or "auto" in combined.lower(), (
        f"expected error to mention 'auto', got: {combined!r}"
    )


# ---------------------------------------------------------------------------
# Scenario 5: regression — existing --module <name> behavior is unchanged.
# ---------------------------------------------------------------------------
def test_existing_module_name_still_filters(multi_module_repo, tmp_path):
    """`--module common` filters the inventory to common/ files
    only. (Regression for the sentinel-introduction: the new
    code path must not break the existing string-value path.)
    """
    out_dir = tmp_path / "out"
    main([
        "scan", "--repo", str(multi_module_repo),
        "--out", str(out_dir), "--module", "common",
    ])
    inv = json.loads((out_dir / "repo_inventory.json").read_text(encoding="utf-8"))
    paths = {row["path"] for row in inv}
    assert "common/src/main/java/com/example/Foo.java" in paths
    assert "admin/foo/src/main/java/com/example/Bar.java" not in paths


# ---------------------------------------------------------------------------
# Sentinel constant — pin the value so a rename is intentional.
# ---------------------------------------------------------------------------
def test_module_auto_constant_value():
    assert MODULE_AUTO == "auto"
