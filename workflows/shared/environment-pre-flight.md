# Environment Pre-Flight

**Cross-workflow rules for verifying the runtime environment before any work begins.**

A workflow that needs `mvn` to run but the sandbox has no `mvn` installed will silently burn 30+ minutes before failing. The pre-flight phase exists to catch this **before** the workflow starts doing real work.

## When to run

Every workflow MUST run the pre-flight as its **first phase** (Phase 0.5 or equivalent), immediately after input validation. The pre-flight is allowed to fail fast with `TC-BLK-PreFlight` or `*-BLK-PreFlight` and stop the workflow — the user will install what's missing and re-run.

## What to check

### Universal checks (every workflow, every stack)

| Check | Why |
|---|---|
| `git` on PATH, ≥ 2.20 | Required for clone, worktree, branch operations |
| `curl` on PATH | Required for GitHub API fallback (see `known-errors/github-auth-in-sandbox.md`) |
| GitHub auth token readable from gateway env | Required for any push, PR, or repo inspection |
| Network reachable to the target repo's package registry | Required for `mvn install`, `pip install`, `npm install` |
| Disk free ≥ 5 GB (Maven/Gradle caches + clones can be large) | Prevents mid-build out-of-disk failures |
| Memory free ≥ 2 GB | `mvn` JVM heap, Gradle daemon, etc. need headroom |

### Per-language stack checks

#### Java + Maven

| Check | Required |
|---|---|
| `java` on PATH | ≥ version specified in target's `pom.xml` `<maven.compiler.source>` |
| `javac` on PATH | matches `java` version |
| `JAVA_HOME` set | points to a real JDK |
| `mvn` on PATH | ≥ 3.6 (or `./mvnw` exists and is executable) |
| `<argLine>` in surefire config compatible with JDK | e.g. `--add-opens` flags for Java 17+ |

**Install commands** (no admin required, sandbox-friendly):

```bash
# Adoptium Temurin 21 (fast — 200 MB tarball, 10 sec download)
curl -L -o /tmp/jdk21.tar.gz "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.5%2B11/OpenJDK21U-jdk_x64_linux_hotspot_21.0.5_11.tar.gz"
mkdir -p /data/jdk21 && tar -xzf /tmp/jdk21.tar.gz -C /data/jdk21
export JAVA_HOME=/data/jdk21/jdk-21.0.5+11
export PATH="$JAVA_HOME/bin:$PATH"

# Maven (brew is fast when bottles are available; ~5 min)
brew install maven
# Or: download binary tarball (~30 sec)
curl -L -o /tmp/maven.tar.gz https://archive.apache.org/dist/maven/maven-3/3.9.9/binaries/apache-maven-3.9.9-bin.tar.gz
mkdir -p /data/maven && tar -xzf /tmp/maven.tar.gz -C /data/maven
export PATH="/data/maven/apache-maven-3.9.9/bin:$PATH"
```

**Avoid:** `brew install openjdk@21` when the sandbox's brew prefix doesn't have a prebuilt bottle. It source-compiles OpenSSL 3 + 17 deps (30-60 min). Use the Adoptium tarball instead.

#### Java + Gradle

| Check | Required |
|---|---|
| `java` on PATH | ≥ 17 |
| `gradle` on PATH or `./gradlew` | ≥ version in `wrapper/gradle-wrapper.properties` |

#### Python + pip

| Check | Required |
|---|---|
| `python3` on PATH | ≥ 3.8 |
| `pip` on PATH | ≥ 21 |
| `pytest` (if used) | `python3 -m pytest --version` works |

#### Node + npm

| Check | Required |
|---|---|
| `node` on PATH | ≥ version in `.nvmrc` or `engines` |
| `npm`/`pnpm`/`yarn` on PATH | matches the lockfile present |

#### Go

| Check | Required |
|---|---|
| `go` on PATH | ≥ version in `go.mod` |

### Per-stack assumption checks (must be confirmed by user or evidence)

The workflow should also document and verify stack-specific assumptions that aren't tools but **runtime expectations**:

| Stack | Assumption | How to verify |
|---|---|---|
| Java + Spring | No special config needed | Check for `@SpringBootTest` in tests; verify `application.yml` or `application.properties` exists |
| Java + Hibernate | `hibernate.hbm2ddl.auto` is `validate` (not `create-drop`) for tests | Read the test `application.yml` |
| Java + Lombok | Project enables annotation processing | Read `pom.xml` for `maven-compiler-plugin` `<annotationProcessorPaths>` |
| Python + Django | `DJANGO_SETTINGS_MODULE` is set | Check `manage.py` and `settings.py` |
| Python + Flask | `app.config` has `TESTING=True` in test mode | Check test fixtures |
| Node + Jest | `jest` is in devDependencies | Read `package.json` |

These are **not blockers** — they're notes the workflow records in `SETUP.md` so the user can review them. The pre-flight can warn if a check fails but should not block on these.

## The pre-flight as a phase

The pre-flight phase must:

1. **Detect the language stack** from the URL or repo shape (heuristic: `pom.xml` → Maven, `build.gradle*` → Gradle, `pyproject.toml`/`setup.py` → Python, `package.json` → Node, `go.mod` → Go).
2. **Verify the required tools** for that stack are installed and on PATH.
3. **Fail fast** with a `*-BLK-PreFlight` blocker if anything's missing — listing exactly what's missing, the install command, and the disk cost.
4. **Generate a `SETUP.md`** in the artifacts directory with the environment state.
5. **Update TC-VAL-* gates** to include the pre-flight check (e.g. `TC-VAL-17 [Environment Verified]`).

## The SETUP.md template

```markdown
# Setup Report — <repo-name> <workflow-name>

Generated: <ISO-8601 timestamp>

## Detected Stack
- Language: <lang>
- Build: <build-system>
- Test framework: <frameworks>
- Coverage: <tool>

## Pre-Flight Check Results
| Check | Required | Found | Status |
|---|---|---|---|
| `java` on PATH | ≥ 17 | 21.0.5 (Adoptium at /data/jdk21/...) | ✅ PASS |
| ... | ... | ... | ❌ FAIL |

## Missing Tools — Install Commands
```bash
# <install commands>
```

## Stack Assumption Warnings
- ⚠️ Lombok detected; verify annotation processing is configured.

## Why this matters
Without `<tool>`, the workflow cannot:
- <capability 1>
- <capability 2>

## Proceed
Set ALLOW_DEPENDENCY_INSTALL=true in the workflow inputs, install the missing tools, then re-run. The workflow will resume from the same TODO_test-coverage.md checkpoint.
```

## Cost of skipping the pre-flight

Documented from a real probe of BroadleafCommerce on 2026-06-07:

- Without pre-flight: agent tried `which mvn`, got nothing, started a 30+ min `brew install` (which source-compiles OpenSSL 3 — 30-60 min in this sandbox), killed it after wasting 5+ min, switched to Adoptium tarball for the JDK, gave up on Maven entirely.
- With pre-flight: 30 sec of `which` checks, fail with `TC-BLK-PreFlight`, user installs Maven, re-run starts from the same checkpoint.

**The pre-flight is cheap (30 sec) and prevents hours of wasted work.** Every workflow should have one.

## When NOT to run the pre-flight

The pre-flight is not needed for:
- **Read-only analysis workflows** (e.g. `app-dev-discovery` running in `MODE=analysis`): no builds, no installs.
- **Workflows that explicitly opt out** via a `SKIP_PRE_FLIGHT=true` flag (not currently exposed; for future use).

For everything else, the pre-flight is **mandatory** and the corresponding TC-VAL-* gate is **required** for the workflow to be considered valid.
