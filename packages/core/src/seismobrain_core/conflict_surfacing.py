"""
File: conflict_surfacing.py
Description: Surface conflicting evidence with both sides cited (FR-GEN-10)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-16
Version: 0.1.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ConflictSide:
    evidence_id: str
    claim: str
    revision: str = ""


@dataclass(frozen=True, slots=True)
class ConflictStatement:
    text: str
    evidence_ids: tuple[str, ...]


def surface_conflict(sides: Sequence[ConflictSide]) -> ConflictStatement:
    """State conflicting evidence explicitly with every side cited."""
    if len(sides) < 2:
        raise ValueError("conflict requires at least two sides")
    parts: list[str] = []
    ids: list[str] = []
    for side in sides:
        label = f"{side.claim} [{side.evidence_id}]"
        if side.revision:
            label = f"{side.claim} (rev {side.revision}) [{side.evidence_id}]"
        parts.append(label)
        ids.append(side.evidence_id)
    text = "Conflicting evidence: " + " versus ".join(parts) + "."
    return ConflictStatement(text=text, evidence_ids=tuple(ids))
