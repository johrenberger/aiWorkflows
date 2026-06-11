from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from mutationctl.llm.fake_client import FakeLLMClient
from mutationctl.llm.response_validator import validate_classification_response
from mutationctl.llm.schemas import build_classification_request
from mutationctl.models import (
    LLMClassificationResponse,
    NormalizedMutant,
    SourceContext,
    SurvivorPacket,
)
from mutationctl.state.store import StateStore
from mutationctl.survivors.packet_builder import build_survivor_packet


def _packet() -> SurvivorPacket:
    return SurvivorPacket(
        packet_id="packet-1",
        mutant_id="mutmut-ambiguous-1",
        source_file="src/sample.py",
        line=9,
        operator="unknown_semantic_change",
        original="complex expression",
        mutated="different complex expression",
        mutant_status="SURVIVED",
        source_context=SourceContext("src/sample.py", 5, 12, "9: complex expression", False),
        related_tests=[],
        coverage_context=None,
        size_bytes=200,
        truncated=False,
        evidence=["src/sample.py", "mutmut_survivors_output.txt"],
        status="PASS",
    )


def _response(project_root: Path, filename: str) -> dict:
    path = project_root / "tests" / "fixtures" / "llm" / filename
    return json.loads(path.read_text(encoding="utf-8"))


def test_given_ambiguous_packet_when_llm_request_built_then_schema_contains_constraints_and_taxonomy() -> None:
    request = build_classification_request(_packet(), request_id="llm-req-1")
    assert request.expected_response_schema_version == "1.0"
    assert request.constraints["must_use_evidence"] is True
    assert request.constraints["no_score_invention"] is True
    assert len(request.allowed_classifications) == 7


def test_given_llm_request_when_store_supplied_then_request_is_persisted(tmp_path: Path) -> None:
    store = StateStore(tmp_path)
    store.initialize()
    build_classification_request(_packet(), request_id="llm-req-1", store=store)
    assert store.list_llm_requests()[0]["request_id"] == "llm-req-1"


def test_given_valid_llm_response_when_validated_then_response_is_accepted(
    project_root: Path, tmp_path: Path
) -> None:
    request = build_classification_request(_packet(), request_id="llm-req-1")
    store = StateStore(tmp_path)
    store.initialize()
    validation = validate_classification_response(request, _response(project_root, "valid_classification_response.json"), store)
    assert validation.accepted is True
    assert store.list_survivor_classifications()[0].classifier_type == "llm"


def test_given_llm_response_missing_evidence_when_validated_then_response_is_rejected(
    project_root: Path, tmp_path: Path
) -> None:
    request = build_classification_request(_packet(), request_id="llm-req-1")
    store = StateStore(tmp_path)
    store.initialize()
    validation = validate_classification_response(
        request, _response(project_root, "invalid_missing_evidence_response.json"), store
    )
    assert validation.accepted is False
    assert store.list_survivor_classifications() == []
    assert store.list_llm_validation_results()[0].status == "FAIL"


def test_given_unknown_classification_when_validated_then_response_is_rejected(project_root: Path) -> None:
    request = build_classification_request(_packet(), request_id="llm-req-1")
    validation = validate_classification_response(
        request, _response(project_root, "invalid_unknown_classification_response.json")
    )
    assert validation.accepted is False


def test_given_response_with_mutation_score_when_validated_then_response_is_rejected(project_root: Path) -> None:
    request = build_classification_request(_packet(), request_id="llm-req-1")
    validation = validate_classification_response(
        request, _response(project_root, "invalid_score_invention_response.json")
    )
    assert validation.accepted is False
    assert "mutation_score" in validation.reason


def test_given_fake_llm_client_when_called_repeatedly_then_response_is_deterministic(project_root: Path) -> None:
    request = build_classification_request(_packet(), request_id="llm-req-1")
    configured = _response(project_root, "valid_classification_response.json")
    client = FakeLLMClient(configured)
    assert client.classify(request) == client.classify(request)


def test_given_ambiguous_packet_in_workspace_when_fake_llm_cli_runs_then_response_is_validated(
    project_root: Path, tmp_path: Path
) -> None:
    repo = project_root / "tests" / "fixtures" / "repos" / "python_survivor_context"
    raw = json.loads(
        (project_root / "tests" / "fixtures" / "survivors" / "ambiguous_survivors.json").read_text(
            encoding="utf-8"
        )
    )[0]
    raw["evidence"] = ", ".join(raw["evidence"])
    survivor = NormalizedMutant(**raw)
    store = StateStore(tmp_path)
    store.initialize()
    store.record_surviving_mutant(survivor)
    build_survivor_packet(survivor, repo, store=store)

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "mutationctl",
            "classify-survivors",
            "--workspace",
            str(tmp_path),
            "--fake-llm",
        ],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
    assert '"fake_llm_accepted": 1' in completed.stdout
