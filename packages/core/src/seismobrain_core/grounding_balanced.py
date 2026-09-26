"""
File: grounding_balanced.py
Description: Balanced grounding mode — sentence-buffered release (FR-GEN-05)
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
from enum import StrEnum

from seismobrain_core.sentence_verifier import VerifiedSentence


class GroundingMode(StrEnum):
    BALANCED = "balanced"
    STRICT = "strict"


@dataclass(frozen=True, slots=True)
class ReleasedSentence:
    text: str
    evidence_ids: tuple[str, ...]
    label: str
    warning_badge: bool
    is_final: bool


@dataclass(frozen=True, slots=True)
class GroundingResult:
    sentences: tuple[ReleasedSentence, ...]
    banner: str | None
    mode: GroundingMode


def apply_grounding(
    verified: Sequence[VerifiedSentence],
    *,
    mode: GroundingMode = GroundingMode.BALANCED,
) -> GroundingResult:
    """Release only after verification; balanced keeps unsupported with badge."""
    released: list[ReleasedSentence] = []
    unsupported_count = 0
    for item in verified:
        if mode is GroundingMode.STRICT and item.label == "unsupported":
            continue
        warning = item.label in {"unsupported", "partial", "no_citation"}
        if item.label == "unsupported":
            unsupported_count += 1
        released.append(
            ReleasedSentence(
                text=item.text,
                evidence_ids=item.evidence_ids,
                label=item.label,
                warning_badge=warning and mode is GroundingMode.BALANCED,
                is_final=True,
            )
        )
    banner = None
    if mode is GroundingMode.BALANCED and unsupported_count:
        banner = "Parts of this answer could not be verified"
    if mode is GroundingMode.STRICT and not released:
        banner = "insufficient_evidence"
    return GroundingResult(sentences=tuple(released), banner=banner, mode=mode)
