# Evidence Standards

Every significant finding must include evidence.

## Acceptable Evidence Types

| Evidence Type | Description |
|---|---|
| File evidence | Source/test/config file path and observed gap. |
| Command evidence | Exact command and result. |
| Coverage evidence | Coverage output showing per-file result. |
| Static evidence | Source-to-test mapping or branch/path analysis. |
| CI evidence | Existing workflow command or missing gate. |
| Failure evidence | Error output, failing test, or blocked command. |

## Prohibited Claims

Do not claim:

- Coverage percentage without coverage output.
- Framework usage without config or file evidence.
- A file is safe to exclude without rationale.
- Tests are deterministic without validating time, randomness, order, external services, and shared state.
- Mutation score without actual mutation execution.

## Evidence Format

Use this pattern in ledgers:

```markdown
- **Evidence**:
  - File: `path/to/file`
  - Command: `exact command`
  - Result: `observed result`
  - Rationale: `why this supports the finding`
```
