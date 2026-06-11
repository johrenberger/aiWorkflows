from __future__ import annotations

from mutationctl.models import LLMClassificationRequest, SurvivorPacket
from mutationctl.survivors.schemas import CLASSIFICATION_TAXONOMY

SCHEMA_VERSION = "1.0"
ALLOWED_OUTPUT_FIELDS = [
    "schema_version",
    "request_id",
    "packet_id",
    "mutant_id",
    "classification",
    "confidence",
    "evidence",
    "recommended_action",
    "equivalent_candidate",
    "needs_human_review",
    "rationale",
]


def build_classification_request(
    packet: SurvivorPacket,
    request_id: str,
    allow_production_fixes: bool = False,
    allow_test_changes: bool = False,
    store=None,
) -> LLMClassificationRequest:
    request = LLMClassificationRequest(
        request_id=request_id,
        packet_id=packet.packet_id,
        mutant_id=packet.mutant_id,
        allowed_classifications=list(CLASSIFICATION_TAXONOMY),
        survivor_packet=packet,
        constraints={
            "allow_production_fixes": allow_production_fixes,
            "allow_test_changes": allow_test_changes,
            "must_use_evidence": True,
            "no_score_invention": True,
            "allowed_output_fields": list(ALLOWED_OUTPUT_FIELDS),
        },
        expected_response_schema_version=SCHEMA_VERSION,
    )
    if store is not None:
        store.record_llm_request(request)
    return request
