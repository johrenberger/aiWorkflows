from __future__ import annotations

import re
from pathlib import Path

from mutationctl.models import PatchApplyResult, PatchProposal, PatchSafetyResult

HUNK = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def apply_patch_proposal(proposal: PatchProposal, safety: PatchSafetyResult, workspace: str | Path, store=None) -> PatchApplyResult:
    if not safety.accepted:
        return PatchApplyResult(proposal.proposal_id, "BLOCKED", False, [], "Patch safety validation did not pass", safety.evidence)
    root = Path(workspace).resolve()
    backups = {}
    changed = []
    try:
        for change in proposal.files:
            target = (root / change.path).resolve()
            if root not in target.parents:
                raise ValueError(f"Patch path escapes workspace: {change.path}")
            original = target.read_text(encoding="utf-8")
            backups[change.path] = original
            updated = _apply_file_diff(original, change.diff)
            target.write_text(updated, encoding="utf-8")
            changed.append(change.path)
        result = PatchApplyResult(proposal.proposal_id, "PASS", True, changed, None, changed, backups)
    except Exception as exc:
        for path, content in backups.items():
            (root / path).write_text(content, encoding="utf-8")
        result = PatchApplyResult(proposal.proposal_id, "FAIL", False, [], str(exc), [str(exc)], {})
    if store:
        store.record_patch_apply_result(result)
    return result


def _apply_file_diff(original: str, diff: str) -> str:
    source = original.splitlines(keepends=True)
    output = []
    cursor = 0
    lines = diff.splitlines()
    index = 0
    while index < len(lines):
        match = HUNK.match(lines[index])
        if not match:
            index += 1
            continue
        old_start = int(match.group(1)) - 1
        output.extend(source[cursor:old_start])
        cursor = old_start
        index += 1
        while index < len(lines) and not lines[index].startswith(("@@ ", "diff --git ")):
            line = lines[index]
            if line.startswith(" "):
                if cursor >= len(source) or source[cursor].rstrip("\r\n") != line[1:]:
                    raise ValueError("Patch context does not match workspace")
                output.append(source[cursor]); cursor += 1
            elif line.startswith("-") and not line.startswith("---"):
                if cursor >= len(source) or source[cursor].rstrip("\r\n") != line[1:]:
                    raise ValueError("Patch removal does not match workspace")
                cursor += 1
            elif line.startswith("+") and not line.startswith("+++"):
                output.append(line[1:] + "\n")
            index += 1
    output.extend(source[cursor:])
    return "".join(output)
