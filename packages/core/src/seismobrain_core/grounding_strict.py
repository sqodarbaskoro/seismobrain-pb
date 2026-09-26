"""
File: grounding_strict.py
Description: Strict grounding mode helpers (FR-GEN-05)
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

from seismobrain_core.grounding_balanced import GroundingMode, GroundingResult, apply_grounding
from seismobrain_core.sentence_verifier import VerifiedSentence
from seismobrain_core.typed_refusals import Refusal, RefusalType, make_refusal


def apply_strict_grounding(
    verified: list[VerifiedSentence],
) -> tuple[GroundingResult, Refusal | None]:
    """Unsupported removed; if answer core gone → insufficient_evidence."""
    result = apply_grounding(verified, mode=GroundingMode.STRICT)
    factual = [v for v in verified if v.label != "no_citation"]
    removed = sum(1 for v in factual if v.label == "unsupported")
    if not result.sentences or (
        factual and removed / len(factual) > 0.5 and not any(
            s.label == "supported" for s in result.sentences
        )
    ):
        return result, make_refusal(RefusalType.INSUFFICIENT_EVIDENCE)
    if result.banner == "insufficient_evidence":
        return result, make_refusal(RefusalType.INSUFFICIENT_EVIDENCE)
    return result, None


def may_tighten_mode(current: GroundingMode, requested: GroundingMode) -> bool:
    """Users may tighten never loosen."""
    order = {GroundingMode.BALANCED: 0, GroundingMode.STRICT: 1}
    return order[requested] >= order[current]
