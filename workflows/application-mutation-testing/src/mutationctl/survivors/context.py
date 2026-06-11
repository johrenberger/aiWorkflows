from __future__ import annotations

import re
from pathlib import Path

from mutationctl.models import RelatedTestReference, SourceContext

FUNCTION_PATTERN = re.compile(r"^\s*(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)")


def slice_source_context(source_path: Path, relative_path: str, line: int | None, radius: int = 8) -> SourceContext:
    lines = source_path.read_text(encoding="utf-8").splitlines()
    target = max(1, min(line or 1, len(lines) or 1))
    start = max(1, target - radius)
    end = min(len(lines), target + radius)
    for index in range(target - 1, max(-1, target - radius - 8), -1):
        if index < len(lines) and FUNCTION_PATTERN.match(lines[index]):
            start = min(start, index + 1)
            break
    content = "\n".join(f"{number}: {lines[number - 1]}" for number in range(start, end + 1))
    return SourceContext(relative_path, start, end, content, False)


def discover_related_tests(repo_path: Path, source_file: str, source_context: SourceContext) -> list[RelatedTestReference]:
    source_stem = Path(source_file).stem
    function_name = _source_function_name(source_context)
    candidates = [
        repo_path / "tests" / f"test_{source_stem}.py",
        repo_path / "tests" / Path(source_file).parent.name / f"test_{source_stem}.py",
    ]
    references = []
    for test_path in candidates:
        if not test_path.is_file():
            continue
        lines = test_path.read_text(encoding="utf-8").splitlines()
        functions = _test_functions(lines)
        matching = [
            item for item in functions
            if function_name and function_name in item[0]
        ]
        if not matching:
            matching = functions[:1]
        for test_name, start, end in matching[:2]:
            content = "\n".join(f"{number}: {lines[number - 1]}" for number in range(start, end + 1))
            relative = test_path.relative_to(repo_path).as_posix()
            references.append(
                RelatedTestReference(relative, test_name, start, end, content, [relative, source_file])
            )
    return references


def _source_function_name(context: SourceContext) -> str | None:
    for line in context.content.splitlines():
        match = FUNCTION_PATTERN.match(line.split(": ", 1)[-1])
        if match:
            return match.group(1)
    return None


def _test_functions(lines: list[str]) -> list[tuple[str, int, int]]:
    starts = []
    for index, line in enumerate(lines, 1):
        match = FUNCTION_PATTERN.match(line)
        if match and match.group(1).startswith("test_"):
            starts.append((match.group(1), index))
    results = []
    for position, (name, start) in enumerate(starts):
        end = starts[position + 1][1] - 1 if position + 1 < len(starts) else len(lines)
        while end > start and not lines[end - 1].strip():
            end -= 1
        results.append((name, start, end))
    return results
