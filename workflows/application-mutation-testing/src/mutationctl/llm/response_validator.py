from __future__ import annotations

from mutationctl.llm.schemas import ALLOWED_OUTPUT_FIELDS
from mutationctl.models import (
    LLMClassificationRequest,
    LLMClassificationResponse,
    LLMValidationResult,
    SurvivorClassification,
)
from mutationctl.survivors.schemas import CLASSIFICATION_TAXONOMY, CONFIDENCE_LEVELS

REQUIRED_FIELDS = set(ALLOWED_OUTPUT_FIELDS)


def validate_classification_response(
    request: LLMClassificationRequest,
    raw_response: dict,
    store=None,
) -> LLMValidationResult:
    reason = _validation_error(request, raw_response)
    if reason is not None:
        result = LLMValidationResult(request.request_id, request.packet_id, "FAIL", False, reason)
        if store is not None:
            store.record_llm_response(raw_response, accepted=False)
            store.record_llm_validation_result(result)
        return result

    response = LLMClassificationResponse(**raw_response)
    result = LLMValidationResult(
        request.request_id,
        request.packet_id,
        "PASS",
        True,
        "Response satisfies the classification contract",
        response,
    )
    if store is not None:
        store.record_llm_response(raw_response, accepted=True)
        store.record_llm_validation_result(result)
        store.record_survivor_classification(
            SurvivorClassification(
                classification_id=f"classification-{response.mutant_id}-llm",
                mutant_id=response.mutant_id,
                source_file=request.survivor_packet.source_file,
                line=request.survivor_packet.line,
                operator=request.survivor_packet.operator,
                classification=response.classification,
                confidence=response.confidence,
                evidence=response.evidence,
                recommended_action=response.recommended_action,
                equivalent_candidate=response.equivalent_candidate,
                needs_human_review=response.needs_human_review,
                classifier_type="llm",
                requires_llm_review=False,
                status="PASS",
                reason=response.rationale,
            )
        )
    return result


def _validation_error(request: LLMClassificationRequest, raw: dict) -> str | None:
    unexpected = set(raw) - REQUIRED_FIELDS
    if unexpected:
        return f"Response contains forbidden fields: {', '.join(sorted(unexpected))}"
    missing = REQUIRED_FIELDS - set(raw)
    if missing:
        return f"Response is missing required fields: {', '.join(sorted(missing))}"
    if raw["schema_version"] != request.expected_response_schema_version:
        return "Response schema version does not match request"
    if raw["request_id"] != request.request_id:
        return "Response request_id does not match request"
    if raw["packet_id"] != request.packet_id:
        return "Response packet_id does not match request"
    if raw["mutant_id"] != request.mutant_id:
        return "Response mutant_id does not match request"
    if raw["classification"] not in CLASSIFICATION_TAXONOMY:
        return "Response classification is outside the allowed taxonomy"
    if raw["classification"] not in request.allowed_classifications:
        return "Response classification is not allowed by this request"
    if raw["confidence"] not in CONFIDENCE_LEVELS:
        return "Response confidence must be high, medium, or low"
    if not isinstance(raw["evidence"], list) or not any(str(item).strip() for item in raw["evidence"]):
        return "Response evidence must be non-empty"
    if not str(raw["recommended_action"]).strip():
        return "Response recommended_action must be non-empty"
    if not str(raw["rationale"]).strip():
        return "Response rationale must be non-empty"
    return None
