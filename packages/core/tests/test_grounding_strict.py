"""
File: test_grounding_strict.py
Description: Strict grounding removes unsupported; tighten-only (T4.7)
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

from seismobrain_core.grounding_balanced import GroundingMode
from seismobrain_core.grounding_strict import apply_strict_grounding, may_tighten_mode
from seismobrain_core.sentence_verifier import VerifiedSentence
from seismobrain_core.typed_refusals import RefusalType


def test_strict_removes_unsupported_and_refuses_when_core_gone() -> None:
    verified = [
        VerifiedSentence("Bad [E1]", ("E1",), "unsupported"),
        VerifiedSentence("Also bad [E1]", ("E1",), "unsupported"),
    ]
    result, refusal = apply_strict_grounding(verified)
    assert result.sentences == ()
    assert refusal is not None
    assert refusal.type is RefusalType.INSUFFICIENT_EVIDENCE


def test_users_may_tighten_never_loosen() -> None:
    assert may_tighten_mode(GroundingMode.BALANCED, GroundingMode.STRICT) is True
    assert may_tighten_mode(GroundingMode.STRICT, GroundingMode.BALANCED) is False
