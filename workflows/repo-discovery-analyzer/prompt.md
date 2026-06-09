# OpenClaw Workflow Prompt: Repo Discovery Analyzer Builder

> This file is the canonical prompt for the `repo-discovery-analyzer` workflow.
> It is intended to be used against the repository that will host the analyzer
> implementation.

---

## Mission

Build a reusable deterministic Python 3.10+ CLI named `repo-discovery-analyzer`.

The tool analyzes a local GitHub repository checkout and emits structured JSON
evidence for downstream AI workflows. It must reduce LLM context burden by
performing deterministic discovery, classification, linking, metrics, and
validation before AI synthesis.

Do not modify the target repository being analyzed by the tool. The analyzer
implementation itself may be added to the target implementation repository during
this workflow.

## Required CLI

```bash
repo-discovery-analyzer \
  --repo-path <local-repo-path> \
  --github-url <github-project-url> \
  --commit <commit-hash> \
  --output-dir <output-directory>
```

Optional flags:

- `--include-large-files`
- `--max-file-bytes <bytes>`
- `--json-indent <int>`
- `--fail-on-validation-error`
- `--verbose`

## Required Outputs

The analyzer must write these files into `--output-dir`:

- `analysis_manifest.json`
- `repo_inventory.json`
- `loc_metrics.json`
- `tech_stack.json`
- `entry_points.json`
- `project_structure.json`
- `routes.json`
- `db_schema.json`
- `dependencies.json`
- `integrations.json`
- `tests.json`
- `error_logging.json`
- `security_signals.json`
- `build_deploy.json`
- `hygiene_findings.json`
- `contradiction_candidates.json`
- `github_links.json`
- `validation_report.json`

## Implementation Principles

1. Use only deterministic ordering and machine-readable JSON.
2. Do not run application code, tests, package installs, or builds in the target
   repository.
3. Do not modify the target repository being analyzed by the analyzer.
4. Tolerate partial failure and unreadable files.
5. Keep baseline operation free of required third-party dependencies.
6. Capture warnings and skipped files explicitly.
7. Generate commit-pinned GitHub URLs.
8. Include start/end timestamps and elapsed time in the manifest only.
9. Keep output schemas stable and predictable.

## Target Package Layout

Create the implementation in the target repo as:

```text
.openclaw/tools/repo-discovery-analyzer/
  README.md
  repo_discovery_analyzer/
    __init__.py
    cli.py
    model.py
    io_utils.py
    github_links.py
    inventory.py
    loc_metrics.py
    detectors/
      __init__.py
      stack.py
      entry_points.py
      java_spring.py
      javascript.py
      database.py
      dependencies.py
      testing.py
      security.py
      error_logging.py
      build_deploy.py
      hygiene.py
      contradictions.py
  validation.py
  tests/
    test_cli.py
    test_github_links.py
    test_inventory.py
    test_java_spring_routes.py
    test_javascript_routes.py
    test_security_redaction.py
    test_validation.py
  pyproject.toml
```

## Required Behavior

Implement deterministic detection for:

- repository inventory and exclusions
- LOC and scale metrics
- stack and framework detection
- entry point detection
- routes and API endpoints
- database schema clues
- dependency extraction
- testing signals
- security signals and redaction
- error handling and logging signals
- build/deploy and infrastructure signals
- hygiene and quality findings
- contradiction candidates
- GitHub URL normalization
- validation reporting

## Validation Expectations

The implementation should include validation that checks:

- repo path exists
- output dir exists
- commit provided
- GitHub URL is parseable
- inventory was generated
- at least one file was analyzed
- required JSON files were produced
- evidence paths exist or are marked missing
- every GitHub URL is commit-pinned
- JSON shape is valid enough for downstream consumption
- warnings are collected

If `--fail-on-validation-error` is set, validation failures should exit non-zero.

## Working Discipline

- Use absolute paths when editing or generating files.
- Do not alter the analyzed target repository's contents beyond the analyzer
  implementation files required by this workflow.
- Prefer the repo's existing conventions if an implementation scaffold already
  exists.
- Keep code readable and testable.

## Completion Response

When finished, report:

- implementation paths
- validation status
- any gaps or assumptions
- the top files a maintainer should review first

