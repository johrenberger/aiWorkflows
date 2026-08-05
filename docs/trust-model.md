# Trust model

The Lean kernel is the final checker. Python, package resolvers, CI runners, LLMs, SMT solvers, and JSON files are untrusted input producers.

- A passing Python test validates tooling only.
- Schema validation validates shape only.
- A finite certificate is not a universal statement.
- Theorem-facing generated Lean files must be deterministic and built in CI.
- Dependency revisions are pinned by `lake-manifest.json` after the first `lake update`.
