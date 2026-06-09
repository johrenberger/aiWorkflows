# repo-discovery-analyzer implementation

This directory contains the Python CLI implementation described by the workflow
and the requirements brief.

The package emits deterministic JSON evidence for downstream OpenClaw workflows
without modifying the repository under analysis. After validation, it also
generates `analysis_report.md`, an organized human-readable summary derived only
from the persisted JSON evidence files.
