from __future__ import annotations

from pathlib import Path

from ..models import Config, WorkItemRecord


def render_work_item_markdown(item: WorkItemRecord, config: Config) -> str:
    uncovered_lines = ", ".join(str(x) for x in item.uncovered_lines[:50]) or "none"
    uncovered_branches = ", ".join(item.uncovered_branches[:50]) or "none"
    supporting = "\n".join(f"- {path}" for path in item.supporting_files) or "- none"
    tests = "\n".join(f"- {path}" for path in item.existing_test_files) or "- none"
    criteria = "\n".join(f"- {x}" for x in item.acceptance_criteria)
    body = f"""# Test Work Item {item.work_item_id}

- Source file: `{item.source_path}`
- Language: `{item.language}`
- Module: `{item.module}`
- Current line coverage: `{item.current_line_coverage:.2f}%`
- Current branch coverage: `{item.current_branch_coverage if item.current_branch_coverage is not None else 'n/a'}`
- Uncovered lines: {uncovered_lines}
- Uncovered branches: {uncovered_branches}
- Risk score: `{item.risk_score:.2f}`
- Risk factors: `{item.risk_factors}`
- Existing test files:
{tests}
- Recommended test type: `{item.recommended_test_type}`
- Supporting files:
{supporting}
- Project test conventions: {item.conventions_summary}
- Target validation command: `{item.validation_command}`

## Instructions

- Create meaningful tests, not coverage-only tests.
- Prefer observable behavior assertions.
- Do not modify production code.
- Do not add skipped, todo, or only tests.
- Follow existing style in the repository.
- Update existing tests when that is the better fit.
- Add component or integration tests when a unit test would be mock-heavy.
- Run the validation command after implementing the tests.

## Acceptance Criteria

{criteria}
"""
    if len(body) > config.max_ai_work_item_chars:
        body = body[: config.max_ai_work_item_chars]
    return body


def write_work_item(item: WorkItemRecord, config: Config) -> Path:
    path = Path(item.content_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_work_item_markdown(item, config), encoding="utf-8")
    return path

