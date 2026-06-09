# Output Template

The workflow should leave the target repo with:

- `repo_discovery_analyzer/`
- `tests/`
- `pyproject.toml`
- `README.md`
- any supporting source files required by the requirements

The generated analyzer implementation should be deterministic, machine-readable,
and safe to reuse from other OpenClaw workflows.

Each analyzer run should also create `analysis_report.md` after validation. The
report must be deterministic, derived from the JSON outputs, organized for human
review, and bounded so enterprise-scale findings do not create an unreadable
document.
