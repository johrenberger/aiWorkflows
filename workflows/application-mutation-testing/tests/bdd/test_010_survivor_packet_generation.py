from __future__ import annotations

import json
from pathlib import Path

from mutationctl.models import NormalizedMutant
from mutationctl.state.store import StateStore
from mutationctl.survivors.packet_builder import build_survivor_packet


def _survivor(project_root: Path, index: int = 0) -> NormalizedMutant:
    fixture = project_root / "tests" / "fixtures" / "survivors" / "normalized_survivors.json"
    raw = json.loads(fixture.read_text(encoding="utf-8"))[index]
    raw["evidence"] = ", ".join(raw["evidence"])
    return NormalizedMutant(**raw)


def test_given_survivor_with_existing_source_when_packet_built_then_source_context_included(
    project_root: Path,
) -> None:
    repo = project_root / "tests" / "fixtures" / "repos" / "python_survivor_context"
    packet = build_survivor_packet(_survivor(project_root), repo)
    assert packet.source_context.file_path == "src/sample.py"
    assert "2:     return value > 10" in packet.source_context.content
    assert "src/sample.py" in packet.evidence


def test_given_related_test_file_when_packet_built_then_test_context_included(project_root: Path) -> None:
    repo = project_root / "tests" / "fixtures" / "repos" / "python_survivor_context"
    packet = build_survivor_packet(_survivor(project_root), repo)
    assert packet.related_tests[0].file_path == "tests/test_sample.py"
    assert packet.related_tests[0].test_name == "test_is_large_returns_true_for_large_value"


def test_given_unrelated_repo_files_when_packet_built_then_packet_excludes_unrelated_content(
    project_root: Path,
) -> None:
    repo = project_root / "tests" / "fixtures" / "repos" / "python_survivor_context"
    packet = build_survivor_packet(_survivor(project_root), repo)
    rendered = packet.source_context.content + "".join(item.content for item in packet.related_tests)
    assert "unrelated sentinel" not in rendered


def test_given_context_exceeds_size_limit_when_packet_built_then_packet_is_truncated_deterministically(
    project_root: Path,
) -> None:
    repo = project_root / "tests" / "fixtures" / "repos" / "python_survivor_context"
    first = build_survivor_packet(_survivor(project_root), repo, max_size_bytes=500)
    second = build_survivor_packet(_survivor(project_root), repo, max_size_bytes=500)
    assert first.truncated is True
    assert first.size_bytes <= 500
    assert first == second


def test_given_missing_source_file_when_packet_built_then_blocker_or_failed_packet_recorded(
    project_root: Path, tmp_path: Path
) -> None:
    survivor = _survivor(project_root)
    survivor.source_file = "src/missing.py"
    store = StateStore(tmp_path)
    store.initialize()
    packet = build_survivor_packet(survivor, tmp_path, store=store)
    assert packet is None
    assert store.list_blockers()[0].code == "SURVIVOR_SOURCE_MISSING"


def test_given_packet_when_store_supplied_then_packet_and_json_artifact_are_persisted(
    project_root: Path, tmp_path: Path
) -> None:
    repo = project_root / "tests" / "fixtures" / "repos" / "python_survivor_context"
    store = StateStore(tmp_path)
    store.initialize()
    packet = build_survivor_packet(_survivor(project_root), repo, store=store)
    assert store.list_survivor_packets()[0].packet_id == packet.packet_id
    assert (store.state_dir / "survivor-packets" / f"{packet.packet_id}.json").is_file()
