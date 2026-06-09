# Recovery

If the implementation run stops halfway through:

1. Re-run the workflow against the same target repo and commit.
2. Inspect `.openclaw/repo-discovery-analyzer/` for the last successful stage.
3. Keep any partially generated source files unless they clearly conflict with the
   requirements.
4. Do not delete user-authored changes outside the workflow-owned paths.

Common recovery cases:

- missing `pyproject.toml`
- incomplete `repo_discovery_analyzer/` package
- tests not yet written
- validation failures caused by missing file paths or naming mismatches

