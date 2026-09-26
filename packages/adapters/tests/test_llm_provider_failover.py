"""
File: test_llm_provider_failover.py
Description: Optional secondary LLM provider failover (T4.27)
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

import pytest

from seismobrain_adapters.llm.failover import FailoverLLMGateway
from seismobrain_adapters.llm.gateway import EgressBlockedError, LLMEgressGateway
from seismobrain_adapters.llm.strategies import build_ollama_vllm_provider
from seismobrain_adapters.llm.transport import RecordingTransport
from seismobrain_core.egress_policy import ApprovedProvider, EgressPolicy
from seismobrain_core.ports.llm_provider import (
    LLMCompletion,
    LLMMessage,
    LLMProviderKind,
)


class _FailingProvider:
    kind = LLMProviderKind.OPENAI_COMPATIBLE

    def complete(
        self,
        messages: Sequence[LLMMessage],
        *,
        model_id: str,
        temperature: float = 0.0,
        seed: int | None = 42,
        max_tokens: int = 1024,
    ) -> LLMCompletion:
        raise RuntimeError("primary down")


def test_failover_to_secondary_when_primary_fails() -> None:
    transport = RecordingTransport(
        response={
            "choices": [{"message": {"content": "from-secondary"}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        }
    )
    secondary = build_ollama_vllm_provider(
        base_url="http://localhost:11434/v1",
        api_key="local",
        transport=transport,
    )
    gateway = LLMEgressGateway(
        providers={
            LLMProviderKind.OPENAI_COMPATIBLE: _FailingProvider(),
            LLMProviderKind.OLLAMA_VLLM: secondary,
        },
        policy=EgressPolicy.APPROVED_PROVIDERS,
        approved=(
            ApprovedProvider(kind=LLMProviderKind.OPENAI_COMPATIBLE, model_id="gpt"),
            ApprovedProvider(kind=LLMProviderKind.OLLAMA_VLLM, model_id="llama"),
        ),
    )
    failover = FailoverLLMGateway(
        gateway=gateway,
        primary=LLMProviderKind.OPENAI_COMPATIBLE,
        secondary=LLMProviderKind.OLLAMA_VLLM,
        primary_model="gpt",
        secondary_model="llama",
    )
    result = failover.complete(messages=[LLMMessage(role="user", content="hi")])
    assert result.text == "from-secondary"
    assert result.provider is LLMProviderKind.OLLAMA_VLLM


def test_failover_respects_egress_policy() -> None:
    gateway = LLMEgressGateway(
        providers={
            LLMProviderKind.OPENAI_COMPATIBLE: _FailingProvider(),
        },
        policy=EgressPolicy.LOCAL_ONLY,
    )
    failover = FailoverLLMGateway(
        gateway=gateway,
        primary=LLMProviderKind.OPENAI_COMPATIBLE,
        secondary=LLMProviderKind.OPENAI_COMPATIBLE,
        primary_model="gpt",
        secondary_model="gpt",
    )
    with pytest.raises(EgressBlockedError):
        failover.complete(messages=[LLMMessage(role="user", content="hi")])
