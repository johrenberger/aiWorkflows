# Maven Sub-Module Reactor

**Cross-workflow rules for running Maven builds on multi-module projects.**

The most common silent failure: invoking `-pl parent` only builds the parent's POM, not its sub-modules. The build "succeeds" with `Total time: 13.7 s` because there's nothing to compile at the parent level.

## The broken-by-default pattern

```bash
# ❌ Only builds core/pom.xml, not core/broadleaf-framework/ or other sub-modules
mvn -pl core -am test
```

If `core/pom.xml` has `<packaging>pom</packaging>` and a `<modules>` block, `-pl core` resolves to the parent POM only. The reactor sees one module, builds it (no source code, just the POM), and reports BUILD SUCCESS with no actual compilation.

The first sign of this failure: the surefire test count is 0 or much lower than expected.

## The fix

```bash
# ✅ Starts the reactor at core/pom.xml, includes all sub-modules
mvn -f core/pom.xml -am test
```

The `-f` flag points to a specific POM file, and Maven uses that as the reactor start. From there, all sub-modules in the `<modules>` block are picked up.

Alternatively:

```bash
# ✅ List the sub-modules explicitly
mvn -pl core/broadleaf-framework,core/broadleaf-framework-web,core/broadleaf-profile,core/broadleaf-profile-web -am test
```

But this is fragile (need to know the sub-module names) and doesn't help if the sub-modules have their own sub-sub-modules.

## Detection: is this a multi-module reactor?

```bash
# Check if the parent POM has <packaging>pom</packaging>
grep -A 1 "<packaging>" parent/pom.xml

# Check if the parent POM has a <modules> block
grep -A 5 "<modules>" parent/pom.xml
```

If both are present, this is a multi-module reactor and you need `-f parent/pom.xml`.

## Per-sub-module test presence

Multi-module projects can have wildly different test counts per sub-module:

| Sub-module | Source files | Test files | Why |
|---|---:|---:|---|
| `core/broadleaf-framework` | 763 | 58 | Main framework, has tests |
| `core/broadleaf-framework-web` | 201 | **0** | Web wiring (deferred) |
| `core/broadleaf-profile` | 103 | 1 | Barely tested |
| `core/broadleaf-profile-web` | 34 | **0** | Web wiring (deferred) |

**The pre-flight should detect this and report it** before attempting a build. If a sub-module has 0 tests, the coverage workflow can either:
- Skip it (set `MODULE_LIST` to exclude it)
- Build it (compilation succeeds, but coverage is 0% for all classes)
- Document it as out-of-scope and proceed with the rest

## The `-am` vs `-amd` flag

- `-am` (also-make): build dependencies of the listed modules. For `core/broadleaf-framework`, this builds `common/` (which it depends on).
- `-amd` (also-make-dependents): build dependents of the listed modules. For `core/broadleaf-framework`, this would build `core/broadleaf-framework-web` (which depends on it).

**For a coverage run on `core/broadleaf-framework`, use `-am` only** — you want the framework module's deps to be available, but you don't want to build the entire reactor (which would include `admin/` and other large modules).

## Cross-module test dependencies

A class in `core/broadleaf-framework` may be covered by tests in `core/broadleaf-framework-web` or `integration/`. For a `framework`-only run, those tests don't run, and the coverage appears low. The spec's coverage-provenance column should call this out:

| File | Direct test in `framework/src/test/`? | Test in another module? |
|---|---|---|
| `OrderOfferComparator` | No | Yes (via `ItemOfferProcessorSpec`) |
| `PromotionDiscount` | No | Yes (via `OrderItemTest`) |
| `FulfillmentGroupItemStrategyImpl` | Yes | — |
| `ValidateAndConfirmPaymentActivity` | Yes | — |

A file with only transitive coverage is harder to test in a `framework`-only run (you'd lose coverage if you dropped the indirect test). The test-writing strategy should treat these as "ADD new test" to lock in coverage directly.

## When this runbook is needed

The coverage workflow MUST check this when:
- The target repo is a Maven project
- Any pom.xml has `<packaging>pom</packaging>` AND a `<modules>` block
- The detection is automatic: any multi-module repo triggers this runbook

The TC-VAL-19 and TC-VAL-20 gates are the formal checks.
