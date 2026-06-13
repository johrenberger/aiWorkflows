"""Waiver store: load and apply waivers for CI-blocking findings.

Implements the waiver portion of Core Requirement 12.

A waiver has:
- waiver_id
- finding_id
- owner
- expiration_date
- rationale
- approved_by

Phase 5 loads waivers from a YAML file and integrates them
into the CI gate evaluation.
"""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import yaml

from .models import Waiver


def load_waivers(path: Path) -> list[Waiver]:
    """Load waivers from a YAML file.

    The file may be a list of waiver dicts, or a single dict
    with key 'waivers' containing the list.
    """
    if not path.exists():
        return []
    try:
        data = yaml.safe_load(path.read_text())
    except yaml.YAMLError:
        return []
    if data is None:
        return []
    if isinstance(data, dict):
        items = data.get("waivers", [])
    elif isinstance(data, list):
        items = data
    else:
        return []
    out: list[Waiver] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        try:
            w = Waiver(
                waiver_id=str(item.get("waiver_id", "")),
                finding_id=str(item.get("finding_id", "")),
                owner=str(item.get("owner", "")),
                expiration_date=str(item.get("expiration_date", "")),
                rationale=str(item.get("rationale", "")),
                approved_by=str(item.get("approved_by", "")),
            )
        except Exception:
            continue
        if w.is_valid():
            out.append(w)
    return out


def is_waiver_active(waiver: Waiver, today: date | None = None) -> bool:
    """Return True if the waiver has not expired."""
    if not waiver.expiration_date:
        return False
    today = today or date.today()
    try:
        exp = datetime.strptime(waiver.expiration_date, "%Y-%m-%d").date()
    except ValueError:
        try:
            exp = datetime.fromisoformat(waiver.expiration_date).date()
        except ValueError:
            return False
    return exp >= today


def active_waivers(waivers: list[Waiver], today: date | None = None) -> list[Waiver]:
    """Return only the active (non-expired) waivers."""
    return [w for w in waivers if is_waiver_active(w, today=today)]
