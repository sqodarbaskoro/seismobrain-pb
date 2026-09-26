"""
File: test_egress_security.py
Description: Egress policy checks in security suite (T4.28)
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

from seismobrain_core.egress_policy import EgressPolicy, decide_egress
from seismobrain_core.ports.llm_provider import LLMProviderKind


def test_air_gapped_and_local_only_block_external() -> None:
    decision = decide_egress(
        policy=EgressPolicy.OPEN,
        provider=LLMProviderKind.OPENAI_COMPATIBLE,
        model_id="gpt",
        air_gapped=True,
    )
    assert decision.allowed is False
