from __future__ import annotations

from pathlib import Path
from typing import Sequence

from ..analyzers.coverage_normalizer import parse_jacoco_xml
from ..analyzers.module_detector import detect_language_and_module
from ..analyzers.mutation_analyzer import detect_mutation_tool
from ..analyzers.source_test_mapper import map_source_to_tests
from ..models import AdapterDetection, CommandSpec, CoverageRecord, FileRecord, MutationToolDetection
from .base import BaseAdapter


class JavaJUnitAdapter(BaseAdapter):
    language = "java"

    def detect(self, repo_path: str | Path) -> AdapterDetection:
        repo_path = Path(repo_path)
        evidence = []
        confidence = 0.0
        for candidate in (repo_path / "pom.xml", repo_path / "build.gradle", repo_path / "build.gradle.kts"):
            if candidate.exists():
                evidence.append(candidate.name)
                confidence += 0.4
        for path in repo_path.rglob("*.java"):
            evidence.append(path.name)
            confidence += 0.1
            break
        return AdapterDetection(language="java", adapter="java_junit", confidence=min(confidence, 1.0), evidence=evidence)

    def inventory(self, repo_path: str | Path) -> list[FileRecord]:
        repo_path = Path(repo_path)
        records: list[FileRecord] = []
        for path in repo_path.rglob("*.java"):
            language, module, _ = detect_language_and_module(repo_path, path)
            records.append(FileRecord(path=str(path.relative_to(repo_path)).replace("\\", "/"), language=language, module=module, size=path.stat().st_size))
        return records

    def discover_test_command(self, repo_path: str | Path, module: str) -> CommandSpec:
        repo_path = Path(repo_path)
        if (repo_path / "pom.xml").exists():
            return CommandSpec(command=["mvn", "test"], cwd=str(repo_path), description="Run Maven tests")
        return CommandSpec(command=["./gradlew", "test"], cwd=str(repo_path), description="Run Gradle tests")

    def discover_coverage_command(self, repo_path: str | Path, module: str) -> CommandSpec:
        repo_path = Path(repo_path)
        if (repo_path / "pom.xml").exists():
            return CommandSpec(command=["mvn", "test", "jacoco:report"], cwd=str(repo_path), description="Run Maven with JaCoCo")
        return CommandSpec(command=["./gradlew", "test", "jacocoTestReport"], cwd=str(repo_path), description="Run Gradle with JaCoCo")

    def preflight_coverage_pitfalls(self, repo_path: str | Path) -> list[dict[str, str]]:
        """Detect Maven/Gradle pom patterns that will silently produce empty
        JaCoCo coverage even when the build succeeds. Returns a list of
        findings, each with a `kind` and a `message` field. The caller
        (orchestrator.coverage_generate) should surface these as warnings
        BEFORE invoking `discover_coverage_command`, so the user gets an
        actionable error instead of a "no_report_written" warning at the
        end of a 5-minute Maven run.

        Bug surfaced 2026-06-11 on BroadleafCommerce (PR #13 follow-up).
        The root pom hard-codes:

            <properties>
              <surefire.argLine>--add-opens ...</surefire.argLine>
            </properties>
            <plugin>
              <artifactId>maven-surefire-plugin</artifactId>
              <configuration>
                <argLine>${surefire.argLine}</argLine>   <!-- static -->
              </configuration>
            </plugin>

        The `<argLine>${surefire.argLine}</argLine>` string is statically
        expanded once when Maven parses the pom, before JaCoCo's
        `prepare-agent` (which runs at the `initialize` phase and tries to
        overwrite the property with `-javaagent:.../jacoco.jar`) can
        influence the test JVM. JaCoCo's `report` goal then logs

            [INFO] --- jacoco:0.8.13:report (report) @ <module> ---
            [INFO] Skipping JaCoCo execution due to missing execution data file.

        and no .exec is produced. The pipeline correctly warns at the end
        (PR #23: "no_report_written") but that warning is at the bottom of
        a multi-minute build log and is easy to miss. A preflight finding
        surfaces the issue before any Maven time is spent.

        The fix lives in the target repo's pom. Change the static
        `<argLine>${surefire.argLine}</argLine>` to the late-binding form
        `<argLine>@{surefire.argLine}</argLine>` (surefire >= 2.20; the
        `@{...}` syntax tells the surefire plugin to re-evaluate the
        property at test-execution time, after JaCoCo has populated it
        with the `-javaagent:` flag). The adapter cannot patch the pom
        automatically; that is operator action in the target repo.

        Detection rule: scan every pom.xml under the repo (root +
        modules) for `<argLine>${...}</argLine>` literals inside a
        surefire-plugin configuration. If found, this is a finding.
        """
        import re

        repo_path = Path(repo_path)
        findings: list[dict[str, str]] = []
        if not (repo_path / "pom.xml").exists():
            # Gradle path; the static-argLine pitfall does not apply.
            return findings
        # Match <argLine>${some.property}</argLine> in any pom.xml.
        # This pattern is the smoking gun for the Broadleaf-shaped bug.
        # The late-binding form <argLine>@{some.property}</argLine> is OK
        # and is NOT flagged. Bare <argLine>literal</argLine> is also OK.
        static_argline_re = re.compile(
            r"<argLine>\s*\$\{[^}]+\}\s*</argLine>",
            re.MULTILINE,
        )
        for pom in repo_path.rglob("pom.xml"):
            try:
                text = pom.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for match in static_argline_re.finditer(text):
                findings.append({
                    "kind": "static_surefire_argline_blocks_jacoco",
                    "pom_path": str(pom.relative_to(repo_path)),
                    "match": match.group(0),
                    "fix": (
                        "Change the surefire plugin's <argLine> in this pom from "
                        "<argLine>${surefire.argLine}</argLine> (statically expanded) "
                        "to <argLine>@{surefire.argLine}</argLine> (late-binding, "
                        "surefire >= 2.20). This lets JaCoCo's prepare-agent inject "
                        "the -javaagent:.../jacoco.jar flag into the test JVM. "
                        "Without this change, mvn test jacoco:report exits 0 but "
                        "produces no coverage report."
                    ),
                })
        return findings

    def parse_coverage(self, report_paths: Sequence[str | Path]) -> list[CoverageRecord]:
        records: list[CoverageRecord] = []
        for report in report_paths:
            report = Path(report)
            if report.suffix.lower() == ".xml":
                records.extend(parse_jacoco_xml(report))
        return records

    def find_test_candidates(self, source_file: str | Path) -> list[str]:
        return map_source_to_tests(str(source_file), "java")

    def recommend_supporting_files(self, source_file: str | Path) -> list[str]:
        p = Path(source_file)
        return [str(p.parent / "pom.xml"), str(p.parent / "build.gradle"), str(p.parent / "build.gradle.kts")]

    def detect_mutation_tool(self, repo_path: str | Path, module: str) -> MutationToolDetection:
        return detect_mutation_tool(repo_path, module, "java")

    def discover_mutation_command(self, repo_path: str | Path, module: str, files: Sequence[str | Path]) -> CommandSpec:
        detection = self.detect_mutation_tool(repo_path, module)
        if detection.available:
            return CommandSpec(command=detection.command, cwd=str(repo_path), description="Run Java mutation testing")
        return CommandSpec(command=["mvn", "test"], cwd=str(repo_path), description="Fallback Java test command")

