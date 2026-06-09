# Workflow Notes

This workflow exists to create a deterministic repository discovery analyzer in a
target repo, not to run the analyzer itself.

The target implementation should:

- expose the required CLI flags
- generate the JSON evidence files listed in the requirements
- avoid mutating the target repository during analysis
- remain deterministic and cross-platform
- keep the baseline dependency footprint minimal

The runner follows the same general shape as the other workflow bundles in this
repo:

1. resolve the target repository
2. scaffold a temporary evidence directory
3. invoke the agent with `prompt.md`
4. validate the resulting implementation
5. commit the generated files if validation passes

The workflow prompt is the source of truth for implementation behavior. The
validator is intentionally narrower and only checks that the expected package
layout and top-level implementation files exist.

