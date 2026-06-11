from __future__ import annotations

from mutationctl.models import PatchProposal, TestWeakeningFinding

ASSERTIONS = ("assert ", "expect(", "should", "assertThat", "pytest.raises")


def detect_test_weakening(proposal: PatchProposal) -> list[TestWeakeningFinding]:
    findings = []
    for change in proposal.files:
        if not change.is_test_file:
            continue
        removed = [line[1:] for line in change.diff.splitlines() if line.startswith("-") and not line.startswith("---")]
        added = [line[1:] for line in change.diff.splitlines() if line.startswith("+") and not line.startswith("+++")]
        removed_assertions = [line for line in removed if any(token in line for token in ASSERTIONS)]
        added_assertions = [line for line in added if any(token in line for token in ASSERTIONS)]
        skip_lines = [line for line in added if any(token in line for token in ("pytest.skip", "@pytest.mark.skip", "xfail", ".only("))]
        if removed_assertions and not added_assertions:
            findings.append(TestWeakeningFinding(change.path, "assertion_removal", "Assertions removed without replacement", removed_assertions))
        if skip_lines:
            findings.append(TestWeakeningFinding(change.path, "test_disabled", "Patch disables or narrows test execution", skip_lines))
    return findings
