---
name: valid-skill
artifact_type: skill
purpose: Validate a project's test coverage report and produce a structured Markdown summary.
category: validation
owner: justin
version: "1.0.0"
inputs:
  - name: coverage_report
    type: file
    description: A path to a coverage.xml or lcov.info file
outputs:
  format: markdown
  sections:
    - title
    - top_risks
    - next_actions
dependencies:
  - test-factory
intended_consumers:
  - mutationctl
  - human
quality_level: usable
last_reviewed: 2026-06-13
---

# valid-skill

This skill is a reference implementation for governance tests.
