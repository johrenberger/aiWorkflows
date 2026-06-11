from __future__ import annotations

from mutationctl.models import PatchProposal, PatchSafetyResult
from mutationctl.patches.weakening import detect_test_weakening


def validate_patch_safety(
    proposal: PatchProposal,
    allow_test_changes: bool = False,
    allow_production_fixes: bool = False,
    allow_assertion_removal: bool = False,
    store=None,
) -> PatchSafetyResult:
    reasons = []
    rejected = []
    weakening = detect_test_weakening(proposal)
    production = [item.path for item in proposal.files if item.is_production_file]
    tests = [item.path for item in proposal.files if item.is_test_file]
    mixed = bool(production and tests)
    if proposal.parse_error:
        reasons.append(proposal.parse_error)
    if tests and not allow_test_changes:
        reasons.append("Test changes are disabled")
        rejected.extend(tests)
    if production and not allow_production_fixes:
        reasons.append("Production fixes are disabled")
        rejected.extend(production)
    if mixed:
        reasons.append("Mixed test and production patches require human review")
    if weakening and not allow_assertion_removal:
        reasons.append("Likely test weakening detected")
        rejected.extend(item.path for item in weakening)
    accepted = not reasons
    result = PatchSafetyResult(
        proposal.proposal_id,
        "PASS" if accepted else ("FAIL" if proposal.parse_error or production or weakening else "BLOCKED"),
        accepted,
        reasons,
        sorted(set(rejected)),
        weakening,
        mixed or bool(weakening),
        proposal.evidence + [item.path for item in proposal.files],
    )
    if store:
        store.record_patch_proposal(proposal)
        store.record_patch_safety_result(result)
    return result
