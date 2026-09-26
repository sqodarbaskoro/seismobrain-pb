"""
File: test_support_label_stages.py
Description: Pre-verification and delivered support labels (T3.10)
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

from seismobrain_core.grounding_balanced import ReleasedSentence
from seismobrain_core.sentence_verifier import VerifiedSentence
from seismobrain_core.support_label_stages import record_support_stages


def test_records_pre_and_delivered_rates() -> None:
    pre = [
        VerifiedSentence("a [E1]", ("E1",), "supported"),
        VerifiedSentence("b [E1]", ("E1",), "unsupported"),
    ]
    delivered = [
        ReleasedSentence("a [E1]", ("E1",), "supported", False, True),
        ReleasedSentence("b [E1]", ("E1",), "unsupported", True, True),
    ]
    record = record_support_stages(pre, delivered)
    assert record.pre_supported_rate == 0.5
    assert record.delivered_supported_rate == 0.5
    assert len(record.pre_verification) == 2
    assert len(record.delivered) == 2
