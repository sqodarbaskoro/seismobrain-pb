"""
File: test_research_synthesis.py
Description: Research single synthesis faithfulness ≥ standard (T5.4)
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
from seismobrain_core.research_pool import PooledEvidence
from seismobrain_core.research_synthesis import (
    faithfulness_vs_standard,
    synthesize_research_answer,
)
from seismobrain_core.sentence_verifier import VerifiedSentence


def test_research_synthesis_faithfulness_at_least_standard() -> None:
    evidence = [
        PooledEvidence("E1", "c1", "Torque is 40 Nm for flange P2/94.", 1.0, ("sq1",)),
        PooledEvidence("E2", "c2", "Seal procedure requires PPE.", 0.8, ("sq2",)),
    ]
    research = synthesize_research_answer(
        question="torque and seal",
        evidence=evidence,
        draft="Torque is 40 Nm [E1]. Seal procedure requires PPE [E2].",
        mode=GroundingMode.STRICT,
        standard_supported_ratio=0.5,
    )
    assert research.faithfulness_ok is True
    standard = [
        VerifiedSentence("Torque is 40 Nm [E1].", ("E1",), "supported"),
        VerifiedSentence("Something weak [E2].", ("E2",), "unsupported"),
    ]
    assert faithfulness_vs_standard(research, standard) is True
