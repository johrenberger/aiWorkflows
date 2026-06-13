"""Story 021: JaCoCo static-argLine late-binding fix.

The existing test in `test_coverage_generation.py`
(`test_preflight_detects_static_surefire_argline_in_pom`) pins the
POSITIVE case: a pom with `<argLine>${surefire.argLine}</argLine>`
(static form) produces a `static_surefire_argline_blocks_jacoco`
finding.

This file pins the NEGATIVE case: a pom with the late-binding form
`<argLine>@{surefire.argLine}</argLine>` produces ZERO findings,
because the JaCoCo `prepare-agent` flag actually flows into the
forked test JVM when argLine is late-bound.

It also pins the mixed case (some sites fixed, some not) and the
profile case (a static form inside a profile that is not the default
build profile).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from test_factory.adapters.java_junit import JavaJUnitAdapter


def _write_pom(tmp_path: Path, surefire_argline: str) -> Path:
    """Write a minimal pom.xml with the given <argLine> value in the
    surefire plugin configuration.
    """
    pom = tmp_path / "pom.xml"
    pom.write_text(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.example</groupId>
  <artifactId>fixture</artifactId>
  <version>1.0.0</version>
  <build>
    <plugins>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-surefire-plugin</artifactId>
        <version>3.2.1</version>
        <configuration>
          <argLine>{surefire_argline}</argLine>
        </configuration>
      </plugin>
    </plugins>
  </build>
</project>
""",
        encoding="utf-8",
    )
    return pom


def _finding_kinds(findings: list[dict]) -> set[str]:
    return {f.get("kind") for f in findings}


# ---------------------------------------------------------------------------
# Scenario 4: preflight no longer fires after the fix (negative case).
# ---------------------------------------------------------------------------
def test_preflight_does_not_fire_when_argline_is_late_bound(tmp_path):
    """A pom with `<argLine>@{surefire.argLine}</argLine>` (late-binding
    form) must produce ZERO `static_surefire_argline_blocks_jacoco`
    findings. The `@{...}` syntax tells surefire to re-evaluate the
    property at fork time, so JaCoCo's `prepare-agent` flag actually
    flows into the test JVM.
    """
    _write_pom(tmp_path, "@{surefire.argLine}")
    findings = JavaJUnitAdapter().preflight_coverage_pitfalls(tmp_path)
    static_findings = [
        f for f in findings
        if f.get("kind") == "static_surefire_argline_blocks_jacoco"
    ]
    assert static_findings == [], (
        f"late-binding pom should produce zero static-argLine findings, "
        f"got: {static_findings!r}"
    )


# ---------------------------------------------------------------------------
# Mixed case: a repo with both the static and late-binding forms. The
# preflight must still fire for the static site (and NOT report the
# late-binding site as a false positive).
# ---------------------------------------------------------------------------
def test_preflight_finds_only_static_site_in_mixed_repo(tmp_path):
    """A repo with both static and late-binding forms (e.g. a partially
    fixed target): the preflight must report the static site and stay
    silent on the late-binding site. This pins that the preflight does
    not have a false-positive on the `@{...}` form.
    """
    # The preflight short-circuits if there is no root pom.xml (it is
    # a Maven-only check). Write an empty root pom to satisfy that
    # gate; the test cares about the two sub-module poms.
    (tmp_path / "pom.xml").write_text(
        '<?xml version="1.0"?><project><modelVersion>4.0.0</modelVersion></project>',
        encoding="utf-8",
    )
    module_static = tmp_path / "module-static"
    module_static.mkdir()
    _write_pom(module_static, "${surefire.argLine}")
    module_late = tmp_path / "module-late"
    module_late.mkdir()
    _write_pom(module_late, "@{surefire.argLine}")
    findings = JavaJUnitAdapter().preflight_coverage_pitfalls(tmp_path)
    static_kinds = _finding_kinds(findings)
    assert "static_surefire_argline_blocks_jacoco" in static_kinds, (
        f"preflight must fire on the static site, got: {findings!r}"
    )
    pom_paths = {f.get("pom_path") for f in findings}
    assert any("module-static" in p for p in pom_paths), (
        f"expected the static module's pom in findings, got: {pom_paths!r}"
    )
    assert not any("module-late" in p for p in pom_paths), (
        f"late-binding module must not be reported, got: {pom_paths!r}"
    )


# ---------------------------------------------------------------------------
# Profile case: a static form inside a profile that is not the default
# build profile. The preflight should still fire (we don't know which
# profile the user is going to activate) but with a `profile` annotation
# so the user knows the context.
# ---------------------------------------------------------------------------
def test_preflight_annotates_findings_inside_profiles(tmp_path):
    """A static argLine inside a `<profile>` is still a real bug if
    that profile is active during the build. The preflight must fire
    and annotate the finding with the profile id so the user knows
    the context. (Without the annotation, the user might fix the
    non-profile surefire config and wonder why the warning persists.)
    """
    pom = tmp_path / "pom.xml"
    pom.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.example</groupId>
  <artifactId>fixture</artifactId>
  <version>1.0.0</version>
  <profiles>
    <profile>
      <id>jrebel-debug</id>
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
    </profile>
  </profiles>
</project>
""",
        encoding="utf-8",
    )
    findings = JavaJUnitAdapter().preflight_coverage_pitfalls(tmp_path)
    static_findings = [
        f for f in findings
        if f.get("kind") == "static_surefire_argline_blocks_jacoco"
    ]
    assert len(static_findings) >= 1, (
        f"preflight must fire on the profile-scoped static argLine, got: {findings!r}"
    )
    profile_fields = {f.get("profile") for f in static_findings}
    assert "jrebel-debug" in profile_fields, (
        f"finding must annotate the profile id, got profile={profile_fields!r}"
    )


# ---------------------------------------------------------------------------
# Regression: the existing positive-case test still works (the
# preflight's regex for the static form is unchanged).
# ---------------------------------------------------------------------------
def test_preflight_still_fires_on_static_form(tmp_path):
    """Sanity: a pom with the static form must still fire the
    preflight. This is the same as
    `test_preflight_detects_static_surefire_argline_in_pom` in
    `test_coverage_generation.py`; duplicated here so that story 021's
    test file is self-contained.
    """
    _write_pom(tmp_path, "${surefire.argLine}")
    findings = JavaJUnitAdapter().preflight_coverage_pitfalls(tmp_path)
    static_findings = [
        f for f in findings
        if f.get("kind") == "static_surefire_argline_blocks_jacoco"
    ]
    assert len(static_findings) == 1, (
        f"static argLine should fire exactly one finding, got: {static_findings!r}"
    )
