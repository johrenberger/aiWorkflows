from __future__ import annotations

from mutationctl.models import NormalizedMutant, SurvivorClassification
from mutationctl.survivors.schemas import CLASSIFICATION_TAXONOMY

RULES = {
    "conditional_boundary": ("Missing edge case", "high", "Add boundary value test"),
    "boolean_negation": ("Untested branch", "medium", "Add opposite-branch test"),
    "conditional_expression": ("Untested branch", "medium", "Add opposite-branch test"),
    "string_replacement": ("Missing assertion", "high", "Assert exact returned value or output"),
    "number_replacement": ("Missing assertion", "high", "Assert exact returned value or output"),
    "constant_replacement": ("Missing assertion", "high", "Assert exact returned value or output"),
    "exception_removal": ("Missing error-path test", "high", "Add error-path assertion"),
    "error_condition": ("Missing error-path test", "medium", "Add error-path assertion"),
    "call_removal": ("Missing assertion", "medium", "Assert side effect or collaborator interaction"),
    "mocked_dependency": (
        "Over-mocked behavior",
        "medium",
        "Replace or supplement mock-heavy test with behavior assertion",
    ),
}


def classify_survivor(survivor: NormalizedMutant, store=None) -> SurvivorClassification:
    evidence = [part.strip() for part in survivor.evidence.split(",") if part.strip()]
    if not evidence:
        result = _result(
            survivor,
            None,
            None,
            [],
            "",
            False,
            True,
            "BLOCKED",
            "Classification requires evidence",
        )
    elif survivor.operator in RULES:
        classification, confidence, action = RULES[survivor.operator]
        if classification not in CLASSIFICATION_TAXONOMY:
            raise ValueError(f"Unsupported classification: {classification}")
        result = _result(
            survivor,
            classification,
            confidence,
            evidence,
            action,
            False,
            False,
            "PASS",
            None,
        )
    else:
        result = _result(
            survivor,
            None,
            "low",
            evidence,
            "Route survivor packet to bounded LLM review",
            False,
            True,
            "DEFERRED",
            "No deterministic rule reached medium confidence",
        )
    if store is not None:
        store.record_survivor_classification(result)
    return result


def _result(
    survivor,
    classification,
    confidence,
    evidence,
    action,
    equivalent,
    requires_llm,
    status,
    reason,
) -> SurvivorClassification:
    return SurvivorClassification(
        classification_id=f"classification-{survivor.mutant_id}-deterministic",
        mutant_id=survivor.mutant_id,
        source_file=survivor.source_file,
        line=survivor.line,
        operator=survivor.operator,
        classification=classification,
        confidence=confidence,
        evidence=evidence,
        recommended_action=action,
        equivalent_candidate=equivalent,
        needs_human_review=False,
        classifier_type="deterministic",
        requires_llm_review=requires_llm,
        status=status,
        reason=reason,
    )
