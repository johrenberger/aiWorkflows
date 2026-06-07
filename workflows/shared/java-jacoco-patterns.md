# Java + JaCoCo Patterns

**Cross-workflow rules for running JaCoCo 0.8.x with Maven 3.9.x and JDK 17+.**

The most common JaCoCo failure mode: the agent is silently never attached because the surefire `<argLine>` config evaluates at parse time, before `prepare-agent` runs.

## The broken-by-default pattern

```xml
<plugin>
  <groupId>org.apache.maven.plugins</groupId>
  <artifactId>maven-surefire-plugin</artifactId>
  <configuration>
    <argLine>${surefire.argLine}</argLine>
  </configuration>
</plugin>

<plugin>
  <groupId>org.jacoco</groupId>
  <artifactId>jacoco-maven-plugin</artifactId>
  <executions>
    <execution>
      <id>default-prepare-agent</id>
      <goals><goal>prepare-agent</goal></goals>
    </execution>
  </executions>
</plugin>
```

**What goes wrong:** `prepare-agent` runs at parse time (during `validate`/`initialize` phase). It sets the `surefire.argLine` property to include `-javaagent:.../jacocoagent.jar=destfile=.../target/jacoco.exec`. But the surefire plugin's `<argLine>${surefire.argLine}</argLine>` is resolved at parse time too — *before* `prepare-agent` runs. So the value is empty, and the agent is never attached.

You'll see this in the surefire report: tests run, but `target/jacoco.exec` doesn't exist, and the `jacoco:report` step says "Skipping JaCoCo execution due to missing execution data file."

## The fix (two options)

### Option 1: Command-line override (recommended for the coverage workflow)

Pass `-Dsurefire.argLine` on the command line. Maven evaluates this when the user-property is read, which is *after* the POM's argLine is parsed:

```bash
mvn -pl core -am test jacoco:report \
  -Dsurefire.argLine="-javaagent:$(find ~/.m2/repository -name 'org.jacoco.agent-0.8.*-runtime.jar' | head -1)=destfile=\${project.basedir}/target/jacoco.exec --add-opens java.base/java.lang=ALL-UNNAMED --add-opens java.base/java.util=ALL-UNNAMED"
```

The `${project.basedir}` interpolation handles per-sub-module destfiles (so each sub-module gets its own `jacoco.exec`).

### Option 2: Use `@{argLine}` (late-binding)

If you can modify the POM, change the surefire config to use the late-binding `@{...}` syntax:

```xml
<argLine>@{argLine}</argLine>
```

This makes surefire read the `argLine` user property at fork time, which is after `prepare-agent` has set it. But this requires a POM change, which the coverage workflow's `ALLOW_PRODUCTION_FIXES=false` rule forbids.

## JaCoCo 0.8.13 + JDK 17+ flags

For modules with Spring, Hibernate, or any module that uses reflection or `MethodHandles`, you need:

```
--add-opens java.base/java.lang=ALL-UNNAMED
--add-opens java.base/java.util=ALL-UNNAMED
```

Without these, surefire tests will fail with `IllegalAccessError` or `InaccessibleObjectException`.

For JDK 21+, you may also need:

```
--add-opens java.base/java.lang.reflect=ALL-UNNAMED
--add-opens java.base/java.io=ALL-UNNAMED
--add-opens java.base/java.net=ALL-UNNAMED
```

## Multi-module JaCoCo reports

When running JaCoCo on a multi-module Maven project, each sub-module produces its own `jacoco.exec`. To aggregate:

```bash
# Each sub-module has its own report at core/<sub-module>/target/site/jacoco/index.html
# Aggregate: use `mvn -pl core -am jacoco:report-aggregate` (JaCoCo 0.8.8+)
```

The `jacoco:report-aggregate` goal produces a single report across all sub-modules. This is the right goal for a coverage workflow's "produce a final report" step.

## Debugging checklist

When `jacoco.exec` doesn't appear:

1. **Check the JaCoCo agent path exists** — `find ~/.m2/repository -name 'org.jacoco.agent-*-runtime.jar'`
2. **Check the surefire argLine is non-empty** — `mvn -X ...` (debug) will show the resolved argLine
3. **Check JDK compatibility** — JaCoCo 0.8.7+ supports JDK 17, JaCoCo 0.8.8+ supports JDK 21 (with `--add-opens`)
4. **Check for the parse-time argLine trap** — see the broken-by-default pattern above
5. **Check the surefire execution** — `target/surefire-reports/*.txt` should exist; if not, tests didn't even run

## When this runbook is needed

The coverage workflow MUST check this when:
- The target repo is a Maven project (any sub-module, not just Spring/Hibernate)
- The `pom.xml` has a `jacoco-maven-plugin` configured
- The detection is automatic: any pom with `org.jacoco:jacoco-maven-plugin` triggers this runbook

The TC-VAL-18 gate is the formal check.
