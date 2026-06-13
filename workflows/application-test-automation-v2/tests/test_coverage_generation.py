from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from test_factory.orchestrator import TestFactoryOrchestrator


# ---------------------------------------------------------------------------
# Regression: preflight diagnostic for the Broadleaf-shaped JaCoCo bug
# ---------------------------------------------------------------------------
#
# Bug surfaced 2026-06-11 on BroadleafCommerce (a 13-module Maven monorepo)
# via the new `release-readiness` / `test-gap-analysis` skills in
# johrenberger/test-repo PR #13. The root pom hard-codes
#
#   <properties>
#     <surefire.argLine>--add-opens ...</surefire.argLine>
#   </properties>
#   <plugin>
#     <artifactId>maven-surefire-plugin</artifactId>
#     <configuration>
#       <argLine>${surefire.argLine}</argLine>   <!-- static -->
#     </configuration>
#   </plugin>
#
# JaCoCo's `prepare-agent` runs at `initialize` and tries to write
# `-javaagent:.../jacoco.jar` into the `surefire.argLine` property.
# But surefire's `<argLine>${surefire.argLine}</argLine>` is statically
# expanded once when Maven parses the pom, so the test JVM runs without
# the agent. JaCoCo's `report` goal logs
#
#   [INFO] --- jacoco:0.8.13:report (report) @ <module> ---
#   [INFO] Skipping JaCoCo execution due to missing execution data file.
#
# and no .exec is produced. The pipeline correctly emits a
# `no_report_written` warning at the end (PR #23), but only after a
# multi-minute Maven build. Pre-flight detection surfaces the issue
# BEFORE Maven runs.
#
# Earlier fix attempt (adding `-DargLine=@{surefire.argLine}` to the
# mvn CLI) did NOT work. The surefire plugin caches its static argLine
# at pom-parse time, and the system property override does not flow
# back into that cached value. The fix must happen in the target
# repo's pom: change `<argLine>${surefire.argLine}</argLine>` to
# `<argLine>@{surefire.argLine}</argLine>` (late-binding; surefire
# >= 2.20).
#
# The fix lives in `JavaJUnitAdapter.preflight_coverage_pitfalls`.
# These tests pin the new contract.
def test_preflight_detects_static_surefire_argline_in_pom(tmp_path):
    """`JavaJUnitAdapter.preflight_coverage_pitfalls` must detect the
    Broadleaf-shaped `<argLine>${...}</argLine>` pattern in any pom.xml
    under the repo, and return a finding with the pom path, the
    matched text, and an actionable fix message.

    Without the preflight, a user running `test-factory run
    --generate-coverage` on a Broadleaf-shaped repo would only see
    a 'no_report_written' warning at the end of a 5-minute Maven run.
    The preflight makes the issue visible at the START of the run.
    """
    from test_factory.adapters.java_junit import JavaJUnitAdapter

    # A pom that exhibits the bug (static surefire <argLine>).
    buggy_pom = tmp_path / "pom.xml"
    buggy_pom.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.example</groupId>
  <artifactId>buggy</artifactId>
  <version>1.0.0</version>
  <build>
    <plugins>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-surefire-plugin</artifactId>
        <configuration>
          <argLine>${surefire.argLine}</argLine>
        </configuration>
      </plugin>
    </plugins>
  </build>
</project>
""",
        encoding="utf-8",
    )
    findings = JavaJUnitAdapter().preflight_coverage_pitfalls(tmp_path)
    assert len(findings) == 1, f"expected 1 finding, got {findings!r}"
    f = findings[0]
    assert f["kind"] == "static_surefire_argline_blocks_jacoco"
    assert f["pom_path"] == "pom.xml"
    assert "${surefire.argLine}" in f["match"]
    # The fix message must name the late-binding alternative.
    assert "@{surefire.argLine}" in f["fix"]
    # The fix message must mention the symptom.
    assert "no coverage" in f["fix"].lower() or "no .exec" in f["fix"].lower() or "Skipping" in f["fix"]


def test_preflight_ignores_late_binding_argline_in_pom(tmp_path):
    """A pom that already uses the late-binding form
    `<argLine>@{surefire.argLine}</argLine>` (the correct pattern) must
    NOT trigger the preflight. The user has already fixed the issue.
    """
    from test_factory.adapters.java_junit import JavaJUnitAdapter

    fixed_pom = tmp_path / "pom.xml"
    fixed_pom.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.example</groupId>
  <artifactId>fixed</artifactId>
  <version>1.0.0</version>
  <build>
    <plugins>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-surefire-plugin</artifactId>
        <configuration>
          <argLine>@{surefire.argLine}</argLine>
        </configuration>
      </plugin>
    </plugins>
  </build>
</project>
""",
        encoding="utf-8",
    )
    findings = JavaJUnitAdapter().preflight_coverage_pitfalls(tmp_path)
    assert findings == [], f"expected no findings on a fixed pom, got {findings!r}"


def test_preflight_ignores_literal_argline_in_pom(tmp_path):
    """A pom that uses a literal `<argLine>--add-opens ...</argLine>`
    (no property reference) must NOT trigger the preflight. The
    late-binding form is only one valid pattern; a literal argLine
    is also acceptable for the purposes of the JaCoCo agent
    injection (JaCoCo's prepare-agent will append its own agent
    flag via `argLine` set on a system property, and the literal
    argLine here just adds --add-opens flags).
    """
    from test_factory.adapters.java_junit import JavaJUnitAdapter

    fixed_pom = tmp_path / "pom.xml"
    fixed_pom.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.example</groupId>
  <artifactId>literal</artifactId>
  <version>1.0.0</version>
  <build>
    <plugins>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-surefire-plugin</artifactId>
        <configuration>
          <argLine>--add-opens java.base/java.lang=ALL-UNNAMED</argLine>
        </configuration>
      </plugin>
    </plugins>
  </build>
</project>
""",
        encoding="utf-8",
    )
    findings = JavaJUnitAdapter().preflight_coverage_pitfalls(tmp_path)
    assert findings == [], f"expected no findings on a literal-argLine pom, got {findings!r}"


def test_preflight_returns_no_findings_on_pomless_repo(tmp_path):
    """If the repo has no pom.xml at the root, the static-argLine
    pitfall does not apply (Gradle path is unaffected). The preflight
    must return an empty list, not crash.
    """
    from test_factory.adapters.java_junit import JavaJUnitAdapter

    # tmp_path exists but has no pom.xml inside it.
    (tmp_path / "build.gradle").write_text("plugins { id 'java' }\n", encoding="utf-8")
    findings = JavaJUnitAdapter().preflight_coverage_pitfalls(tmp_path)
    assert findings == []


def test_preflight_finds_pattern_in_nested_module_pom(tmp_path):
    """Multi-module Maven repos can have the static argLine in a
    child pom, not the root. The preflight must rglob all pom.xml
    files in the repo, not just the root.
    """
    from test_factory.adapters.java_junit import JavaJUnitAdapter

    # Root pom is clean.
    (tmp_path / "pom.xml").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.example</groupId>
  <artifactId>parent</artifactId>
  <version>1.0.0</version>
  <packaging>pom</packaging>
  <modules><module>child</module></modules>
</project>
""",
        encoding="utf-8",
    )
    # Child pom has the bug.
    child_dir = tmp_path / "child"
    child_dir.mkdir()
    (child_dir / "pom.xml").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <parent>
    <groupId>com.example</groupId>
    <artifactId>parent</artifactId>
    <version>1.0.0</version>
  </parent>
  <artifactId>child</artifactId>
  <build>
    <plugins>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-surefire-plugin</artifactId>
        <configuration>
          <argLine>${argLine}</argLine>
        </configuration>
      </plugin>
    </plugins>
  </build>
</project>
""",
        encoding="utf-8",
    )
    findings = JavaJUnitAdapter().preflight_coverage_pitfalls(tmp_path)
    assert len(findings) == 1
    assert findings[0]["pom_path"] == "child/pom.xml"
    assert "${argLine}" in findings[0]["match"]


def test_coverage_generate_attaches_preflight_findings_to_result(tmp_path):
    """End-to-end: when `generate_coverage=True` is set on `run()`, the
    orchestrator must call `preflight_coverage_pitfalls` and attach the
    findings to the `generation` record. This makes the warnings
    visible in the artifact JSON and in the final report, BEFORE Maven
    runs (or at least before the warning is gated on exit code 0).
    """
    repo = _copy_fixture_repo(tmp_path)
    out_dir = tmp_path / "analysis-artifacts"
    orchestrator = TestFactoryOrchestrator(repo, out_dir)
    try:
        from test_factory.adapters.java_junit import JavaJUnitAdapter
        from test_factory.models import CommandSpec

        # The sample-repo fixture is a Python repo; force the primary
        # adapter to JavaJUnitAdapter so the preflight (which lives on
        # JavaJUnitAdapter) is exercised end-to-end. Replace the
        # sample-repo's pom.xml with a buggy one so the preflight has
        # something to find.
        (repo / "pom.xml").write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.example</groupId>
  <artifactId>buggy</artifactId>
  <version>1.0.0</version>
  <build>
    <plugins>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-surefire-plugin</artifactId>
        <configuration>
          <argLine>${surefire.argLine}</argLine>
        </configuration>
      </plugin>
    </plugins>
  </build>
</project>
""",
            encoding="utf-8",
        )
        java_adapter = JavaJUnitAdapter()
        # Patch the orchestrator to use JavaJUnitAdapter as the primary
        # adapter. We do this by monkey-patching _primary_adapter.
        original_primary = orchestrator._primary_adapter
        orchestrator._primary_adapter = lambda adapter_name=None: java_adapter
        # Patch the adapter to a no-op command so the test doesn't
        # need real Maven. We only care that preflight_findings is
        # attached to the result before/after the command.
        original_command = java_adapter.discover_coverage_command
        java_adapter.discover_coverage_command = lambda repo_path, module: CommandSpec(
            command=["true"],
            cwd=str(repo),
            description="no-op for preflight test",
        )
        try:
            result = orchestrator.run(limit=1, module="package", generate_coverage=True)
        finally:
            java_adapter.discover_coverage_command = original_command
            orchestrator._primary_adapter = original_primary
        gen = result["coverage_generation"]
        assert gen is not None
        preflight = gen["generation"].get("preflight_findings", [])
        # The preflight must have run BEFORE the command and found the
        # static-argLine pattern.
        assert any(f.get("kind") == "static_surefire_argline_blocks_jacoco" for f in preflight), (
            f"preflight_findings missing or wrong shape: {preflight!r}"
        )
    finally:
        orchestrator.close()


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_REPO = PROJECT_ROOT / "tests" / "fixtures" / "sample-repo"


def _copy_fixture_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "sample-repo"
    shutil.copytree(FIXTURE_REPO, repo)
    return repo


def test_coverage_generate_is_on_by_default_in_run_story020(tmp_path):
    """Story 020: `run()` now invokes `discover_coverage_command` by
    default. The PR #23 contract was "off by default, opt-in via
    generate_coverage=True"; story 020 flips that to "on by default,
    opt-out via generate_coverage=False". This test pins the new
    default. The explicit opt-in path is covered by
    `test_coverage_generate_runs_adapter_command_when_enabled`
    below (which passes generate_coverage=True); the explicit opt-out
    path is covered by `test_no_generate_coverage_flag_skips_generation`
    in `test_020_v2_default_generate_coverage.py`.
    """
    repo = _copy_fixture_repo(tmp_path)
    out_dir = tmp_path / "analysis-artifacts"
    orchestrator = TestFactoryOrchestrator(repo, out_dir)
    try:
        result = orchestrator.run(limit=2, module="package")
        # Story 020: coverage_generation is now a real dict by default,
        # not None. Status may be 'ok', 'no_report_written', 'error', or
        # 'skipped' — any of those means generation was ATTEMPTED.
        # Shape: {"generation": {"status": ..., ...}, "records": [...]}
        assert result["coverage_generation"] is not None, (
            "Story 020 default is ON: coverage_generation must be a dict, not None"
        )
        gen_inner = result["coverage_generation"].get("generation", result["coverage_generation"])
        assert gen_inner.get("status") in {
            "ok", "no_report_written", "error", "failed", "skipped"
        }, f"unexpected coverage_generation status: {result['coverage_generation']!r}"
        # The coverage_runs/ artifact dir SHOULD now exist (orchestrator
        # called coverage_generate).
        assert (out_dir / "coverage_runs").exists()
    finally:
        orchestrator.close()


def test_coverage_generate_runs_adapter_command_when_enabled(tmp_path):
    """When `generate_coverage=True`, run() invokes the primary adapter's
    `discover_coverage_command` to actually produce a coverage report. We
    patch whichever adapter _primary_adapter() selects for the fixture
    repo and verify:
    1. coverage_generate returns a generation record
    2. the artifact file is written
    3. coverage records are parsed (the post-generation records may
       be empty if no report is produced, but the call must not crash)
    """
    repo = _copy_fixture_repo(tmp_path)
    # The fixture repo has pre-existing coverage reports (coverage.xml,
    # coverage-final.json, lcov.info) used by other tests. For THIS test
    # we want to verify the new-report detection, so wipe them first.
    for stale in repo.rglob("coverage.xml"):
        if stale.is_file():
            stale.unlink()
    for stale in repo.rglob("coverage-final.json"):
        if stale.is_file():
            stale.unlink()
    for stale in repo.rglob("lcov.info"):
        if stale.is_file():
            stale.unlink()
    for stale in repo.rglob("jacoco.xml"):
        if stale.is_file():
            stale.unlink()
    out_dir = tmp_path / "analysis-artifacts"
    orchestrator = TestFactoryOrchestrator(repo, out_dir)
    try:
        from test_factory.models import CommandSpec

        primary = orchestrator._primary_adapter()
        assert primary is not None, "fixture should have a detectable primary language"
        coverage_script = repo / "fake_coverage.py"
        coverage_script.write_text(
            "from pathlib import Path\n"
            "xml = '''<coverage><packages><package name=\"package\"><classes><class filename=\"package/foo.py\"><lines><line number=\"1\" hits=\"1\"/><line number=\"2\" hits=\"1\" branch=\"true\" condition-coverage=\"100% (2/2)\"/></lines></class></classes></package></packages></coverage>'''\n"
            "Path('coverage.xml').write_text(xml, encoding='utf-8')\n",
            encoding="utf-8",
        )
        original = primary.discover_coverage_command
        primary.discover_coverage_command = lambda repo_path, module: CommandSpec(
            command=[sys.executable, str(coverage_script)],
            cwd=str(repo),
            description="fixture coverage generator",
        )
        try:
            result = orchestrator.run(limit=2, module="package", generate_coverage=True)
        finally:
            primary.discover_coverage_command = original
        gen = result["coverage_generation"]
        assert gen is not None
        assert gen["generation"]["status"] == "completed"
        assert gen["generation"]["exit_code"] == 0
        assert any("coverage.xml" in p for p in gen["generation"].get("new_reports", []))
        # After generation, parsed records should include the package/foo.py
        # entry from the freshly-written coverage.xml.
        paths = {r["path"] for r in gen["records"]}
        assert "package/foo.py" in paths
        # The artifact file was written.
        assert (out_dir / "coverage_runs" / "generate.json").exists()
    finally:
        orchestrator.close()


def test_coverage_generate_handles_missing_binary(tmp_path):
    """If the adapter's discover_coverage_command references a binary
    that doesn't exist, coverage_generate must record a clean failure
    and not crash the pipeline."""
    repo = _copy_fixture_repo(tmp_path)
    out_dir = tmp_path / "analysis-artifacts"
    orchestrator = TestFactoryOrchestrator(repo, out_dir)
    try:
        from test_factory.models import CommandSpec

        primary = orchestrator._primary_adapter()
        assert primary is not None
        original = primary.discover_coverage_command
        primary.discover_coverage_command = lambda repo_path, module: CommandSpec(
            command=["definitely-not-a-real-binary-xyz"],
            cwd=str(repo),
            description="missing binary",
        )
        try:
            result = orchestrator.run(limit=1, module="package", generate_coverage=True)
        finally:
            primary.discover_coverage_command = original
        gen = result["coverage_generation"]
        assert gen is not None
        assert gen["generation"]["status"] == "missing_binary"
        assert gen["generation"]["exit_code"] == 127
        # Pipeline must still complete with status=ok
        assert result["status"] == "ok"
    finally:
        orchestrator.close()


def test_coverage_generate_detects_overwritten_reports(tmp_path):
    """Regression for Bug #6 (PR #26): the post-run check from PR #23
    used path-identity diff (`post - pre`) to detect new reports, so a
    pre-existing coverage.json that pytest-cov rewrote in place looked
    like 'nothing was written' and emitted a false-positive
    `no_report_written` warning. The fix uses mtime comparison: a
    report is "new" if its post-run mtime is strictly newer than the
    pre-run snapshot.

    This test pre-creates coverage.json / coverage.xml / .coverage
    with an OLD mtime (simulating stale reports in the repo), then
    runs the orchestrator with a patched adapter that rewrites them
    in place. The expected behavior is: status=completed, all 3
    reports listed in new_reports, no warning.
    """
    import os
    import time

    repo = _copy_fixture_repo(tmp_path)
    # Wipe any pre-existing coverage artifacts in the fixture copy
    for stale in repo.rglob("coverage.json"):
        if stale.is_file():
            stale.unlink()
    for stale in repo.rglob("coverage.xml"):
        if stale.is_file():
            stale.unlink()
    for stale in repo.rglob(".coverage"):
        if stale.is_file():
            stale.unlink()
    out_dir = tmp_path / "analysis-artifacts"
    orchestrator = TestFactoryOrchestrator(repo, out_dir)
    try:
        from test_factory.models import CommandSpec

        primary = orchestrator._primary_adapter()
        assert primary is not None
        # Pre-create all 3 reports with a very old mtime (7 days ago).
        # The orchestrator's pre-run snapshot will pick these up.
        old_mtime = time.time() - 86400 * 7
        for name in ("coverage.json", "coverage.xml", ".coverage"):
            target = repo / name
            target.write_text("stale content that pytest-cov should overwrite", encoding="utf-8")
            os.utime(target, (old_mtime, old_mtime))
        # Patch the adapter to a script that REWRITES all 3 reports
        # in place at the same paths (not new files).
        coverage_script = repo / "fake_coverage_overwrite.py"
        coverage_script.write_text(
            "import os, time, json\n"
            "from pathlib import Path\n"
            "# Write a minimal valid coverage.py JSON shape so the\n"
            # orchestrator's coverage() step (which re-parses the report\n"
            # after generation) doesn't crash. The shape is what\n"
            # `coverage json` produces, with one file covered.\n"
            "payload = {\n"
            "    'meta': {'version': '7.4.4', 'timestamp': '2026-06-11'},\n"
            "    'files': {'package/foo.py': {'summary': {'percent_covered': 100.0}, 'executed_lines': [1, 2], 'missing_lines': [], 'executed_branches': [], 'missing_branches': []}},\n"
            "    'totals': {'percent_covered': 100.0, 'covered_lines': 2, 'num_statements': 2, 'missing_lines': 0, 'excluded_lines': 0, 'num_branches': 0, 'num_partial_branches': 0, 'covered_branches': 0, 'missing_branches': 0}\n"
            "}\n"
            "Path('coverage.json').write_text(json.dumps(payload), encoding='utf-8')\n"
            "Path('coverage.xml').write_text('<coverage/>', encoding='utf-8')\n"
            "Path('.coverage').write_bytes(b'newer coverage data')\n"
            "# Touch all 3 with a fresh mtime (clearly newer than the 7-day-old one)\n"
            "for name in ('coverage.json', 'coverage.xml', '.coverage'):\n"
            "    os.utime(Path(name), None)\n",
            encoding="utf-8",
        )
        original = primary.discover_coverage_command
        primary.discover_coverage_command = lambda repo_path, module: CommandSpec(
            command=[sys.executable, str(coverage_script)],
            cwd=str(repo),
            description="fake coverage that overwrites pre-existing reports in place",
        )
        try:
            result = orchestrator.run(limit=1, module="package", generate_coverage=True)
        finally:
            primary.discover_coverage_command = original
        gen = result["coverage_generation"]
        assert gen is not None
        # Status must be completed, NOT no_report_written. This is
        # the regression assertion: under the old (buggy) code, the
        # 3 rewritten-in-place reports would not appear in
        # new_reports, status would be no_report_written, and a
        # warning would be emitted.
        assert gen["generation"]["status"] == "completed", (
            f"expected 'completed' (pre-existing reports were rewritten in place), "
            f"got {gen['generation']['status']!r} with warning: "
            f"{gen['generation'].get('warning', '(none)')}"
        )
        # All 3 reports must be listed as new.
        new_reports = gen["generation"].get("new_reports", [])
        assert any("coverage.json" in p for p in new_reports), (
            f"coverage.json should be in new_reports: {new_reports}"
        )
        assert any("coverage.xml" in p for p in new_reports), (
            f"coverage.xml should be in new_reports: {new_reports}"
        )
        assert any(".coverage" in p for p in new_reports), (
            f".coverage should be in new_reports: {new_reports}"
        )
        # No warning.
        assert "warning" not in gen["generation"], (
            f"no warning expected: {gen['generation'].get('warning')!r}"
        )
    finally:
        orchestrator.close()
