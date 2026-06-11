from __future__ import annotations

import hashlib
import re
from pathlib import Path

from mutationctl.models import PatchFileChange, PatchProposal

DIFF_HEADER = re.compile(r"^diff --git a/(.+) b/(.+)$")


def is_test_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    name = Path(normalized).name
    return (
        normalized.startswith(("tests/", "test/", "src/test/"))
        or "/tests/" in f"/{normalized}"
        or "/src/test/" in f"/{normalized}"
        or name.startswith("test_") and name.endswith(".py")
        or name.endswith(("_test.py", ".test.js", ".spec.js", ".test.ts", ".spec.ts"))
    )


def parse_patch(path: str | Path) -> PatchProposal:
    patch_path = Path(path)
    text = patch_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    changes = []
    starts = [index for index, line in enumerate(lines) if DIFF_HEADER.match(line)]
    parse_error = None
    if not starts:
        parse_error = "Patch contains no valid diff --git headers"
    else:
        starts.append(len(lines))
        for offset in range(len(starts) - 1):
            block = lines[starts[offset]:starts[offset + 1]]
            match = DIFF_HEADER.match(block[0])
            if match is None or not any(line.startswith("@@ ") for line in block):
                parse_error = "Patch contains malformed file diff"
                break
            old_path, new_path = match.groups()
            if old_path != new_path:
                change_type = "rename"
            elif any(line.startswith("--- /dev/null") for line in block):
                change_type = "add"
            elif any(line.startswith("+++ /dev/null") for line in block):
                change_type = "delete"
            else:
                change_type = "modify"
            test_file = is_test_path(new_path)
            changes.append(PatchFileChange(new_path, change_type, "\n".join(block) + "\n", test_file, not test_file))
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    return PatchProposal(
        f"patch-{digest}", "fixture", [], [], changes, "Validate proposed test hardening",
        "Strengthen tests without production changes", [str(patch_path)], parse_error
    )
