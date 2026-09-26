"""
File: test_grounding_balanced.py
Description: Balanced grounding sentence-buffered release (T3.6)
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

from seismobrain_core.grounding_balanced import GroundingMode, apply_grounding
from seismobrain_core.sentence_verifier import VerifiedSentence


def test_balanced_releases_unsupported_with_badge() -> None:
    verified = [
        VerifiedSentence("Ok [E1]", ("E1",), "supported"),
        VerifiedSentence("Bad [E1]", ("E1",), "unsupported"),
    ]
    result = apply_grounding(verified, mode=GroundingMode.BALANCED)
    assert all(s.is_final for s in result.sentences)
    assert len(result.sentences) == 2
    assert result.sentences[1].warning_badge is True
    assert result.banner is not None


def test_strict_drops_unsupported() -> None:
    verified = [
        VerifiedSentence("Ok [E1]", ("E1",), "supported"),
        VerifiedSentence("Bad [E1]", ("E1",), "unsupported"),
    ]
    result = apply_grounding(verified, mode=GroundingMode.STRICT)
    assert len(result.sentences) == 1
    assert result.sentences[0].label == "supported"
