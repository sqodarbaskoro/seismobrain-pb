"""
File: test_degraded_balanced.py
Description: Degraded badge when reranker/verifier unavailable in balanced (T3.31)
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

from seismobrain_core.degraded import DegradedFlags, apply_degraded_balanced
from seismobrain_core.grounding_balanced import GroundingMode, apply_grounding
from seismobrain_core.sentence_verifier import VerifiedSentence


def test_balanced_answers_with_degraded_badge() -> None:
    verified = [VerifiedSentence("Ok [E1]", ("E1",), "supported")]
    grounding = apply_grounding(verified, mode=GroundingMode.BALANCED)
    result = apply_degraded_balanced(
        grounding, flags=DegradedFlags(reranker=False, verifier=False)
    )
    assert result.degraded is True
    assert result.badge == "degraded"
    assert result.grounding.sentences
