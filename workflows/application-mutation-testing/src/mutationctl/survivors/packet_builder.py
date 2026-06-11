from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from mutationctl.models import Blocker, NormalizedMutant, SurvivorPacket
from mutationctl.survivors.context import discover_related_tests, slice_source_context


def build_survivor_packet(
    survivor: NormalizedMutant,
    repo_path: str | Path,
    coverage_context: dict | None = None,
    max_size_bytes: int = 12000,
    store=None,
) -> SurvivorPacket | None:
    root = Path(repo_path)
    source_path = root / survivor.source_file
    if not source_path.is_file():
        if store is not None:
            store.record_blocker(
                Blocker(
                    "SURVIVOR_SOURCE_MISSING",
                    "BLOCKED",
                    "Survivor source file does not exist",
                    survivor.source_file,
                )
            )
        return None

    source_context = slice_source_context(source_path, survivor.source_file, survivor.line)
    related_tests = discover_related_tests(root, survivor.source_file, source_context)
    evidence = [survivor.source_file]
    if survivor.evidence:
        evidence.extend(part.strip() for part in survivor.evidence.split(",") if part.strip())
    evidence.extend(reference.file_path for reference in related_tests)
    packet = SurvivorPacket(
        packet_id=_packet_id(survivor),
        mutant_id=survivor.mutant_id,
        source_file=survivor.source_file,
        line=survivor.line,
        operator=survivor.operator,
        original=survivor.original,
        mutated=survivor.mutated,
        mutant_status=survivor.status,
        source_context=source_context,
        related_tests=related_tests,
        coverage_context=coverage_context,
        size_bytes=0,
        truncated=False,
        evidence=list(dict.fromkeys(evidence)),
        status="PASS",
    )
    _truncate_packet(packet, max_size_bytes)
    if store is not None:
        store.record_survivor_packet(packet)
    return packet


def _packet_id(survivor: NormalizedMutant) -> str:
    identity = f"{survivor.mutant_id}|{survivor.source_file}|{survivor.line}|{survivor.operator}"
    return f"packet-{hashlib.sha256(identity.encode('utf-8')).hexdigest()[:12]}"


def _packet_size(packet: SurvivorPacket) -> int:
    payload = asdict(packet)
    payload["size_bytes"] = 0
    return len(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _truncate_packet(packet: SurvivorPacket, max_size_bytes: int) -> None:
    packet.size_bytes = _packet_size(packet)
    if packet.size_bytes <= max_size_bytes:
        return
    packet.truncated = True
    while packet.related_tests and _packet_size(packet) > max_size_bytes:
        packet.related_tests.pop()
    content = packet.source_context.content
    while content and _packet_size(packet) > max_size_bytes:
        content = content[:-32]
        packet.source_context.content = content
        packet.source_context.truncated = True
    while packet.evidence and _packet_size(packet) > max_size_bytes:
        packet.evidence.pop()
    packet.size_bytes = _packet_size(packet)
