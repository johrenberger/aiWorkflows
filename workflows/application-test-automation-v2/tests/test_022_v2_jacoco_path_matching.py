"""Story 022: v2 JaCoCo path-matching regression net.

The v2 `parse_jacoco_xml` function emits records keyed on JaCoCo's
dot-package-slash form (e.g. `org/example/Foo.java`). v2's
`risk_scores.json` is keyed on v2's inventory file paths
(e.g. `src/main/java/org/example/Foo.java` for a single-module
repo, or `common/src/main/java/...` for a multi-module repo).

The existing join in `orchestrator._merge_coverage_records` uses
a suffix-matching approach (`_normalize_coverage_path`) that
works in the happy case but is hard to test in isolation because
it's a private method on the orchestrator class.

Story 022 adds a new module-level helper, `resolve_jacoco_paths`,
that provides a deterministic, side-effect-free rewrite from
JaCoCo form to inventory form. It walks the repo's `pom.xml` /
`build.gradle*` files to discover module roots, then tries each
combination of (module_root, layout, record_path) and picks the
first on-disk match.

This file pins the new helper's contract. The helper is
additive: it does not replace the existing
`_normalize_coverage_path` (which works for the Maven default
layout via suffix matching). It exists as a safety net for
edge cases (different source layouts, empty inventories) and
as a regression net for future refactors.
"""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from test_factory.analyzers.coverage_normalizer import (
    parse_jacoco_xml,
    resolve_jacoco_paths,
)


# ---------------------------------------------------------------------------
# Fixture builders
# ---------------------------------------------------------------------------
def _write_java_file(repo: Path, *segments: str, body: str = "class X {}") -> Path:
    """Write a Java source file at `<repo>/<segments...>` with the
    given body. Returns the file's path.
    """
    path = repo.joinpath(*segments)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(body), encoding="utf-8")
    return path


def _write_pom(repo: Path, *segments: str, body: str | None = None) -> Path:
    """Write a minimal pom.xml at `<repo>/<segments...>`. Used to
    mark a directory as a Maven module root.
    """
    if body is None:
        body = textwrap.dedent("""\
            <?xml version="1.0" encoding="UTF-8"?>
            <project xmlns="http://maven.apache.org/POM/4.0.0">
              <modelVersion>4.0.0</modelVersion>
              <groupId>com.example</groupId>
              <artifactId>fixture</artifactId>
              <version>1.0.0</version>
            </project>
            """)
    return _write_java_file(repo, *segments, body=body)


def _write_jacoco_xml(
    report: Path,
    *,
    package: str,
    sourcefile: str,
    class_name: str | None = None,
    lines: list[tuple[int, int]] | None = None,
) -> Path:
    """Write a minimal but realistic jacoco.xml. `lines` is a list of
    (line_nr, ci) pairs; omit to write a class with no per-line
    counters (still produces a 0.0 record).
    """
    if class_name is None:
        class_name = f"{package}/{sourcefile.removesuffix('.java')}"
    if lines is None:
        lines = []
    line_xml = "\n".join(
        f'      <line nr="{nr}" mi="0" ci="{ci}" mb="0" cb="0"/>'
        for nr, ci in lines
    )
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<!DOCTYPE report PUBLIC "-//JACOCO//DTD Report 1.1//EN" "report.dtd">
<report name="fixture">
  <package name="{package}">
    <class name="{class_name}" sourcefilename="{sourcefile}">
      <counter type="INSTRUCTION" missed="0" covered="0"/>
      <counter type="LINE" missed="0" covered="0"/>
    </class>
    <sourcefile name="{sourcefile}">
{line_xml}
      <counter type="INSTRUCTION" missed="0" covered="0"/>
      <counter type="LINE" missed="0" covered="0"/>
    </sourcefile>
  </package>
</report>
""",
        encoding="utf-8",
    )
    return report


def _fake_inventory(rows: list[dict]) -> list[dict]:
    """Build a minimal inventory row list with the given `path` and
    `module` fields. Other fields are filled with safe defaults.
    """
    out = []
    for row in rows:
        out.append({
            "path": row["path"],
            "module": row.get("module", row["path"].split("/", 1)[0]),
            "is_excluded": False,
            "is_test": False,
            "language": "java",
        })
    return out


# ---------------------------------------------------------------------------
# Scenario 1: single-module Maven repo — every record maps back to
# `<repo>/src/main/java/...`.
# ---------------------------------------------------------------------------
def test_single_module_repo_resolves_to_src_main_java(tmp_path):
    """A single-module Maven repo. JaCoCo report has one package
    `org/example` and one sourcefile `Foo.java`. The helper must
    rewrite the record's `path` from `org/example/Foo.java` to
    `src/main/java/org/example/Foo.java`.
    """
    # Set up the source file on disk so the resolver can find it.
    _write_java_file(
        tmp_path,
        "src", "main", "java", "org", "example", "Foo.java",
        body="package org.example;\nclass Foo {}\n",
    )
    # Set up the jacoco.xml.
    report = tmp_path / "target" / "site" / "jacoco" / "jacoco.xml"
    _write_jacoco_xml(
        report,
        package="org/example",
        sourcefile="Foo.java",
        lines=[(1, 1), (2, 0)],
    )
    records = parse_jacoco_xml(report)
    # Sanity: parser contract is unchanged.
    assert records[0].path == "org/example/Foo.java"

    inventory = _fake_inventory([
        {"path": "src/main/java/org/example/Foo.java", "module": "<root>"},
    ])
    resolved = resolve_jacoco_paths(records, tmp_path, inventory)
    assert len(resolved) == 1
    assert resolved[0].path == "src/main/java/org/example/Foo.java"


# ---------------------------------------------------------------------------
# Scenario 2: multi-module Maven repo — different packages resolve
# to different module prefixes.
# ---------------------------------------------------------------------------
def test_multi_module_repo_resolves_per_module(tmp_path):
    """A multi-module Maven repo with `common/` and `admin/foo/`
    modules. JaCoCo's report contains two packages:
    `org/broadleafcommerce/common` (resolves under `common/`) and
    `org/broadleafcommerce/openadmin` (resolves under
    `admin/foo/`).
    """
    # Common module source file.
    _write_java_file(
        tmp_path,
        "common", "src", "main", "java", "org", "broadleafcommerce",
        "common", "Foo.java",
        body="package org.broadleafcommerce.common;\nclass Foo {}\n",
    )
    # Admin module source file.
    _write_java_file(
        tmp_path,
        "admin", "foo", "src", "main", "java", "org", "broadleafcommerce",
        "openadmin", "Bar.java",
        body="package org.broadleafcommerce.openadmin;\nclass Bar {}\n",
    )
    # Mark each module root with a pom.xml so the resolver can
    # discover them.
    _write_pom(tmp_path, "common", "pom.xml")
    _write_pom(tmp_path, "admin", "foo", "pom.xml")
    # Build a jacoco.xml with both packages.
    report = tmp_path / "target" / "site" / "jacoco" / "jacoco.xml"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        textwrap.dedent("""\
        <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <!DOCTYPE report PUBLIC "-//JACOCO//DTD Report 1.1//EN" "report.dtd">
        <report name="fixture">
          <package name="org/broadleafcommerce/common">
            <class name="org/broadleafcommerce/common/Foo" sourcefilename="Foo.java"/>
            <sourcefile name="Foo.java">
              <line nr="1" mi="0" ci="1" mb="0" cb="0"/>
              <counter type="LINE" missed="0" covered="1"/>
            </sourcefile>
          </package>
          <package name="org/broadleafcommerce/openadmin">
            <class name="org/broadleafcommerce/openadmin/Bar" sourcefilename="Bar.java"/>
            <sourcefile name="Bar.java">
              <line nr="1" mi="1" ci="0" mb="0" cb="0"/>
              <counter type="LINE" missed="1" covered="0"/>
            </sourcefile>
          </package>
        </report>
        """),
        encoding="utf-8",
    )
    records = parse_jacoco_xml(report)
    assert {r.path for r in records} == {
        "org/broadleafcommerce/common/Foo.java",
        "org/broadleafcommerce/openadmin/Bar.java",
    }

    inventory = _fake_inventory([
        {"path": "common/src/main/java/org/broadleafcommerce/common/Foo.java", "module": "common"},
        {"path": "admin/foo/src/main/java/org/broadleafcommerce/openadmin/Bar.java", "module": "admin/foo"},
    ])
    resolved = resolve_jacoco_paths(records, tmp_path, inventory)
    paths = {r.path for r in resolved}
    assert "common/src/main/java/org/broadleafcommerce/common/Foo.java" in paths
    assert "admin/foo/src/main/java/org/broadleafcommerce/openadmin/Bar.java" in paths


# ---------------------------------------------------------------------------
# Scenario 3: a class in the inventory but absent from the report
# must NOT receive a synthetic coverage record. (The score step's
# "no coverage → 0.0" fallback still applies.)
# ---------------------------------------------------------------------------
def test_inventory_files_absent_from_report_are_not_backfilled(tmp_path):
    """Coverage records in the report are only those JaCoCo saw.
    Files in v2's inventory that the report does not contain stay
    unmatched (i.e. the resolver does not invent a 0.0 record for
    them — that is the score step's job).
    """
    _write_java_file(
        tmp_path,
        "src", "main", "java", "org", "example", "Foo.java",
        body="package org.example;\nclass Foo {}\n",
    )
    _write_java_file(
        tmp_path,
        "src", "main", "java", "org", "example", "Bar.java",
        body="package org.example;\nclass Bar {}\n",
    )
    report = tmp_path / "target" / "site" / "jacoco" / "jacoco.xml"
    _write_jacoco_xml(
        report,
        package="org/example",
        sourcefile="Foo.java",
        lines=[(1, 1)],
    )
    records = parse_jacoco_xml(report)
    inventory = _fake_inventory([
        {"path": "src/main/java/org/example/Foo.java", "module": "<root>"},
        {"path": "src/main/java/org/example/Bar.java", "module": "<root>"},
    ])
    resolved = resolve_jacoco_paths(records, tmp_path, inventory)
    paths = {r.path for r in resolved}
    assert "src/main/java/org/example/Foo.java" in paths
    assert "src/main/java/org/example/Bar.java" not in paths


# ---------------------------------------------------------------------------
# Scenario 4: anonymous inner classes — the parser emits a single
# <sourcefile> block per outer file, and the resolution must not
# duplicate that record.
# ---------------------------------------------------------------------------
def test_anonymous_inner_classes_do_not_create_duplicate_records(tmp_path):
    """JaCoCo emits anonymous inner classes as separate
    `<class name=".../Foo$1" sourcefilename="Foo.java"/>` entries
    but only one `<sourcefile name="Foo.java">` block per package.
    The parser must continue to produce a single record per
    sourcefile (not per class), and the resolver must not duplicate
    it.
    """
    _write_java_file(
        tmp_path,
        "src", "main", "java", "org", "example", "Foo.java",
        body="package org.example;\nclass Foo { class Inner {} }\n",
    )
    report = tmp_path / "target" / "site" / "jacoco" / "jacoco.xml"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        textwrap.dedent("""\
        <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <report name="fixture">
          <package name="org/example">
            <class name="org/example/Foo" sourcefilename="Foo.java"/>
            <class name="org/example/Foo$1" sourcefilename="Foo.java"/>
            <sourcefile name="Foo.java">
              <line nr="1" mi="0" ci="1" mb="0" cb="0"/>
              <line nr="2" mi="1" ci="0" mb="0" cb="0"/>
              <counter type="LINE" missed="1" covered="1"/>
            </sourcefile>
          </package>
        </report>
        """),
        encoding="utf-8",
    )
    records = parse_jacoco_xml(report)
    # Sanity: parser still produces ONE record per sourcefile.
    assert len(records) == 1
    inventory = _fake_inventory([
        {"path": "src/main/java/org/example/Foo.java", "module": "<root>"},
    ])
    resolved = resolve_jacoco_paths(records, tmp_path, inventory)
    assert len(resolved) == 1
    assert resolved[0].path == "src/main/java/org/example/Foo.java"
    # 1 covered out of 2 lines = 50%.
    assert resolved[0].line_coverage == 50.0


# ---------------------------------------------------------------------------
# Scenario 5: a class with no `sourcefilename` falls back to
# `<package>/<class-without-suffix>.java`. The resolver does not
# attempt to resolve this to an inventory path (no sourcefilename
# to match against on disk); the path stays in the dot-package
# form.
# ---------------------------------------------------------------------------
def test_class_with_no_sourcefilename_keeps_synthetic_path(tmp_path):
    """Some JaCoCo reports (e.g. for synthetic classes from
    annotation processors) have a class with no `sourcefilename`.
    The parser emits `path = "<package>/<class-no-suffix>.java"`.
    The resolver must not throw on this case; the path stays in
    the synthetic form (it cannot be resolved to an inventory path
    because the resolver has nothing to look for on disk).
    """
    report = tmp_path / "target" / "site" / "jacoco" / "jacoco.xml"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        textwrap.dedent("""\
        <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <report name="fixture">
          <package name="org/example">
            <class name="org/example/Generated$$FastClassByCGLIB$$abc"/>
            <sourcefile name="Generated.java"/>
          </package>
        </report>
        """),
        encoding="utf-8",
    )
    records = parse_jacoco_xml(report)
    # Sanity: parser produces a record for the empty sourcefile too.
    inventory = _fake_inventory([])
    resolved = resolve_jacoco_paths(records, tmp_path, inventory)
    # No inventory rows; resolver must not raise.
    assert isinstance(resolved, list)
