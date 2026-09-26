"""
File: test_egress_policy.py
Description: Data-egress policies local_only / approved_providers (T4.15)
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

import pytest

from seismobrain_adapters.llm import LLMEgressGateway, OpenAICompatibleProvider, RecordingTransport
from seismobrain_adapters.llm.gateway import EgressBlockedError
from seismobrain_adapters.llm.strategies import build_ollama_vllm_provider
from seismobrain_core.egress_policy import ApprovedProvider, EgressPolicy, decide_egress
from seismobrain_core.ports.llm_provider import LLMMessage, LLMProviderKind


def test_local_only_and_approved_providers_block_and_audit() -> None:
    assert (
        decide_egress(
            policy=EgressPolicy.LOCAL_ONLY,
            provider=LLMProviderKind.OPENAI_COMPATIBLE,
            model_id="gpt",
        ).allowed
        is False
    )
    assert (
        decide_egress(
            policy=EgressPolicy.LOCAL_ONLY,
            provider=LLMProviderKind.OLLAMA_VLLM,
            model_id="llama",
        ).allowed
        is True
    )
    approved = (
        ApprovedProvider(kind=LLMProviderKind.ANTHROPIC, model_id="claude-3"),
    )
    assert (
        decide_egress(
            policy=EgressPolicy.APPROVED_PROVIDERS,
            provider=LLMProviderKind.ANTHROPIC,
            model_id="claude-3",
            approved=approved,
        ).allowed
        is True
    )
    assert (
        decide_egress(
            policy=EgressPolicy.APPROVED_PROVIDERS,
            provider=LLMProviderKind.ANTHROPIC,
            model_id="other",
            approved=approved,
        ).allowed
        is False
    )

    transport = RecordingTransport(
        response={
            "choices": [{"message": {"content": "ok"}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        }
    )
    gateway = LLMEgressGateway(
        providers={
            LLMProviderKind.OPENAI_COMPATIBLE: OpenAICompatibleProvider(
                base_url="https://api.openai.com/v1",
                api_key="sk",
                transport=transport,
            ),
            LLMProviderKind.OLLAMA_VLLM: build_ollama_vllm_provider(
                base_url="http://localhost:11434/v1",
                api_key="local",
                transport=transport,
            ),
        },
        policy=EgressPolicy.LOCAL_ONLY,
    )
    with pytest.raises(EgressBlockedError):
        gateway.complete(
            provider=LLMProviderKind.OPENAI_COMPATIBLE,
            messages=[LLMMessage(role="user", content="hi")],
            model_id="gpt",
        )
    assert gateway.audit.entries
    assert gateway.audit.entries[0]["event"] == "egress_blocked"
    ok = gateway.complete(
        provider=LLMProviderKind.OLLAMA_VLLM,
        messages=[LLMMessage(role="user", content="hi")],
        model_id="llama",
    )
    assert ok.text == "ok"


def test_air_gapped_forces_local_only() -> None:
    decision = decide_egress(
        policy=EgressPolicy.OPEN,
        provider=LLMProviderKind.OPENAI_COMPATIBLE,
        model_id="gpt",
        air_gapped=True,
    )
    assert decision.allowed is False
