# Story 021: JaCoCo static-argLine late-binding fix

## Goal

As a target repo (BroadleafCommerce), I should not have a static
`<argLine>${surefire.argLine}</argLine>` in any surefire-plugin
configuration, so that JaCoCo's `prepare-agent` goal can inject the
`-javaagent:.../jacoco.jar` flag into the test JVM and `mvn test
jacoco:report` actually produces a coverage `.exec` file.

## Background

The v2 (test-factory) `JavaJUnitAdapter.preflight_coverage_pitfalls`
function (PR #32) surfaces the `static_surefire_argline_blocks_jacoco`
finding on any target repo that has the Broadleaf-shaped pattern:

```xml
<plugin>
  <artifactId>maven-surefire-plugin</artifactId>
  <configuration>
    <argLine>${surefire.argLine}</argLine>   <!-- static -->
  </configuration>
</plugin>
```

Combined with:

```xml
<plugin>
  <artifactId>jacoco-maven-plugin</artifactId>
  <executions>
    <execution>
      <goals><goal>prepare-agent</goal></goals>
      <configuration>
        <propertyName>surefire.argLine</propertyName>
      </configuration>
    </execution>
  </executions>
</plugin>
```

The result: JaCoCo's `prepare-agent` runs at `initialize` and tries
to write `-javaagent:.../jacoco.jar` into the `surefire.argLine`
property. But surefire's `<argLine>${surefire.argLine}</argLine>` is
**statically expanded** once when Maven parses the pom, so the test
JVM runs without the agent. JaCoCo's `report` goal logs:

```
[INFO] --- jacoco:0.8.13:report (report) @ <module> ---
[INFO] Skipping JaCoCo execution due to missing execution data file.
```

and no `.exec` is produced. Downstream: `risk_scores.json` has
`line_coverage=0.0` everywhere (story 019's signal is degenerate).

The fix: change `<argLine>${surefire.argLine}</argLine>` to
`<argLine>@{surefire.argLine}</argLine>` (surefire late-binding,
requires surefire >= 2.20). With late-binding, surefire re-evaluates
the property every time it forks a test JVM, so the agent flag
injected by JaCoCo's `prepare-agent` is actually picked up.

## Acceptance Scenarios

1. **Root pom uses late-binding form.**
   Given the root `pom.xml` of a target repo
   When the surefire plugin's `<argLine>` is read
   Then it contains `@{surefire.argLine}` (late-binding), not
   `${surefire.argLine}` (static).

2. **All sub-module poms use late-binding form.**
   Given any sub-module `pom.xml` of a target repo
   When the surefire plugin's `<argLine>` is read
   Then it contains `@{surefire.argLine}` (late-binding), not
   `${surefire.argLine}` (static). Profiles are checked too.

3. **Surefire plugin version is >= 2.20.**
   Given the surefire plugin's `<version>` in the root pom
   When read
   Then it is >= 2.20 (the minimum that supports late-binding).

4. **Preflight no longer fires after the fix.**
   Given a target repo with the late-binding form in all surefire
   `<argLine>` configurations
   When v2's `JavaJUnitAdapter.preflight_coverage_pitfalls` runs
   Then it returns zero `static_surefire_argline_blocks_jacoco`
   findings.

5. **Coverage generation actually produces a report.**
   Given a target repo with the late-binding fix applied
   When `mvn test jacoco:report` runs end-to-end
   Then at least one `target/site/jacoco/jacoco.xml` (or `.exec`) is
   written, and `risk_scores.json` has at least one file with a
   non-zero `line_coverage`.

6. **JaCoCo agent flag is in the test JVM's effective argLine.**
   Given a target repo with the late-binding fix
   When `mvn -X test` (or `mvn test -Dargline.print=true`) runs
   Then the surefire-forked JVM's effective argLine includes the
   `-javaagent:.../jacoco.jar` flag.

## Executable Test Mapping

`tests/test_021_jacoco_argline_late_binding.py` — 4 unit tests
covering scenarios 4 (negative case, mixed case, profile case, and
positive-case regression). Scenarios 1-3 and 5 are pom- and
build-level; they run against the BroadleafCommerce checkout.

The scenario 5 success criterion is partially met: a real
`jacoco.exec` is now produced, but v2's coverage parser maps only
5/765 records onto v2's path-graph (a separate parser bug; see
"Out of Scope" below). The Maven-level fix is proven; the v2
parser-level integration is the next story.

## Done Criteria

- BroadleafCommerce root `pom.xml` surefire `<argLine>` is
  `@{surefire.argLine}`.
- BroadleafCommerce `admin/broadleaf-admin-functional-tests/pom.xml`
  surefire `<argLine>` is `@{surefire.argLine}`.
- BroadleafCommerce `integration/pom.xml` JDWP/JRebel profile
  surefire `<argLine>` uses `@{surefire.argLine}` for the JaCoCo
  property part (the rest of the line is left static).
- v2's `JavaJUnitAdapter.preflight_coverage_pitfalls` returns zero
  findings for the fixed Broadleaf.
- v2's preflight now annotates findings inside `<profile>` with the
  profile id (new `profile` field on the finding).
- End-to-end Broadleaf Maven run produces a real `jacoco.exec` and
  a real `target/site/jacoco/jacoco.xml` (proved by running
  `mvn test jacoco:report` on `broadleaf-common` post-fix; the report
  goal logs "Loading execution data file .../jacoco.exec" and
  "Analyzed bundle ... with 817 classes").
- A new v2 BDD test (`tests/test_021_jacoco_argline_late_binding.py`)
  pins the negative case, the mixed-site case, the profile-context
  annotation, and a positive-case regression.
- Existing v2 test `test_preflight_detects_static_surefire_argline_in_pom`
  still passes (positive path is unchanged).

## End-to-End Evidence (Broadleaf, 2026-06-13, post-fix)

Run: `mvn -pl common test jacoco:report` (Broadleaf `broadleaf-common`
module only, due to a flaky MVEL test under load unrelated to story
021).

Result:
- 1/1 test pass (MvelHelperTest#testMvelMethodOverloadFailureCase in
  isolation)
- `Loading execution data file
  /tmp/BroadleafCommerce/common/target/jacoco.exec` (JaCoCo agent
  was injected; the late-binding fix unblocked the test JVM)
- `Analyzed bundle 'BroadleafCommerce Common Libraries' with 817
  classes` (JaCoCo's report goal actually ran)
- `target/site/jacoco/jacoco.xml` was produced with per-class
  `<counter type="INSTRUCTION" .../>` and `<counter type="LINE" .../>`
  data (real `mi=... ci=...` values, not all-zero)

Also: `v2 preflight_coverage_pitfalls(/tmp/BroadleafCommerce)`
returns `[]` findings (was 2 pre-fix: `pom.xml` and
`admin/.../pom.xml`).

A second end-to-end run with the full reactor
(`test-factory run --module admin`) failed at the Maven level on the
flaky MVEL test (1/94 failures), so the
`risk_scores.json` for that run is degenerate (line_coverage=0.0
across the board because no report was generated). This is a real
Broadleaf test bug, not story 021's scope. The Maven-level fix is
proven by the isolated `mvn -pl common` run above.

## Out of Scope (Future Stories)

- v2 JaCoCo path-matching follow-up: v2's coverage parser matches
  JaCoCo's class-name paths against v2's internal module-graph and
  produces only a sparse match (5/765 records mapped on a real
  Broadleaf run). This is a separate parser bug, not story 021.
  Fixing it would unlock the "risk_scores.json has non-zero
  line_coverage end-to-end" success criterion for the full reactor
  (not just `broadleaf-common`).
- Auto-patching poms in arbitrary repos (a `mutationctl fix-pom
  --jacoco-late-binding` command could be added later; this story
  only fixes the three known sites in Broadleaf).
- The flaky MVEL test in `broadleaf-common` (unrelated; tracked
  separately).
- Routing the generated coverage to an external `--out` dir so the
  target repo is not mutated (story 020 follow-up #2).
- Caching the generated coverage across runs.
