from __future__ import annotations

from pathlib import Path

from mutationctl.models import PatchApplyResult, PatchRevertResult


def revert_patch(applied: PatchApplyResult, workspace: str | Path, store=None) -> PatchRevertResult:
    root = Path(workspace).resolve()
    try:
        for path, content in applied.backups.items():
            target = (root / path).resolve()
            if root not in target.parents:
                raise ValueError(f"Backup path escapes workspace: {path}")
            target.write_text(content, encoding="utf-8")
        result = PatchRevertResult(applied.proposal_id, "PASS", True, list(applied.backups), None, list(applied.backups))
    except Exception as exc:
        result = PatchRevertResult(applied.proposal_id, "FAIL", False, [], str(exc), [str(exc)])
    if store:
        store.record_patch_revert_result(result)
    return result
