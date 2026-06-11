# Story 010: Survivor Packet Generation

## Goal

As the workflow, I need compact survivor packets so later analysis is bounded, deterministic, and evidence-based.

## Acceptance Scenarios

- Given an existing source file, when a packet is built, then numbered nearby source context is included.
- Given a related conventional test, when a packet is built, then a focused test reference is included.
- Given unrelated repository files, when a packet is built, then they are excluded.
- Given a packet size limit, when context exceeds it, then truncation is deterministic.
- Given a missing source file, when generation runs, then a blocker is recorded without crashing.

## Executable Test Mapping

`tests/bdd/test_010_survivor_packet_generation.py`

## Done Criteria

- Packet schemas and context slicing exist.
- Packet limits are enforced.
- Packets persist to SQLite and JSON artifacts.
- Missing source files fail safely.
