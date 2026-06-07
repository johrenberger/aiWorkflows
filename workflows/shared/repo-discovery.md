# Repository Discovery

## Purpose

Discover the application stack, test framework, coverage tooling, source layout, and CI configuration without overloading context.

## Safe Discovery Commands

```bash
pwd
git rev-parse --show-toplevel
git rev-parse HEAD
git status --short
find . -maxdepth 4 -type f \
  \( -name 'package.json' -o -name 'pyproject.toml' -o -name 'pytest.ini' -o -name 'tox.ini' -o -name 'pom.xml' -o -name 'build.gradle' -o -name 'go.mod' -o -name '*.csproj' \) | sort
find . -maxdepth 4 -type d \
  \( -name tests -o -name __tests__ -o -name spec -o -name test \) | sort
find . -maxdepth 4 -type f \
  \( -path './.github/workflows/*' -o -name '*coverage*' -o -name 'lcov.info' -o -name 'coverage.xml' \) | sort
```

## File Inspection Priority

Inspect files in this order:

1. Package and build configuration.
2. Test configuration.
3. CI workflows.
4. Existing tests.
5. Source files with no nearby tests.
6. High-risk modules: auth, payment, data integrity, API, database, config, public/client logic.
7. Coverage reports.

## Context Boundaries

For each target module, inspect only:

- The source file.
- Its nearest tests.
- Relevant fixtures/factories/builders.
- Relevant dependency interfaces.
- Relevant framework/test config.

Do not scan unrelated files unless required to understand behavior.
