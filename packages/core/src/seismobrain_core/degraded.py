"""
File: degraded.py
Description: Degradation badges when models unavailable (NFR-REL-04)
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

from dataclasses import dataclass

from seismobrain_core.grounding_balanced import GroundingResult


@dataclass(frozen=True, slots=True)
class DegradedFlags:
    reranker: bool = True
    verifier: bool = True


@dataclass(frozen=True, slots=True)
class DegradedBalancedResult:
    grounding: GroundingResult
    degraded: bool
    badge: str | None


@dataclass(frozen=True, slots=True)
class DegradedStrictResult:
    refused: bool
    refusal_type: str | None


def apply_degraded_balanced(
    grounding: GroundingResult, *, flags: DegradedFlags
) -> DegradedBalancedResult:
    degraded = not (flags.reranker and flags.verifier)
    return DegradedBalancedResult(
        grounding=grounding,
        degraded=degraded,
        badge="degraded" if degraded else None,
    )


def apply_degraded_strict(*, flags: DegradedFlags) -> DegradedStrictResult:
    """Strict mode refuses when reranker or verifier is unavailable."""
    if flags.reranker and flags.verifier:
        return DegradedStrictResult(refused=False, refusal_type=None)
    return DegradedStrictResult(refused=True, refusal_type="service_unavailable")

