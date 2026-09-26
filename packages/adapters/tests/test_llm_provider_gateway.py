"""
File: test_llm_provider_gateway.py
Description: LLMProvider strategies via single egress gateway (T3.1)
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

from seismobrain_adapters.llm import (
    AnthropicProvider,
    GeminiProvider,
    LLMEgressGateway,
    OpenAICompatibleProvider,
    RecordingTransport,
    build_ollama_vllm_provider,
)
from seismobrain_core.ports.llm_provider import LLMMessage, LLMProviderKind


def _openai_response(text: str = "ok [E1]") -> dict:
    return {
        "choices": [{"message": {"content": text}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }


def test_gateway_supports_all_four_provider_strategies() -> None:
    transport = RecordingTransport(response=_openai_response())
    anthropic_transport = RecordingTransport(
        response={
            "content": [{"type": "text", "text": "anthropic [E1]"}],
            "usage": {"input_tokens": 3, "output_tokens": 2},
        }
    )
    gemini_transport = RecordingTransport(
        response={"candidates": [{"content": {"parts": [{"text": "gemini [E1]"}]}}]}
    )
    gateway = LLMEgressGateway(
        providers={
            LLMProviderKind.OPENAI_COMPATIBLE: OpenAICompatibleProvider(
                base_url="https://api.openai.com/v1",
                api_key="sk-test",
                transport=transport,
            ),
            LLMProviderKind.ANTHROPIC: AnthropicProvider(
                base_url="https://api.anthropic.com",
                api_key="ant-test",
                transport=anthropic_transport,
            ),
            LLMProviderKind.GEMINI: GeminiProvider(
                base_url="https://generativelanguage.googleapis.com",
                api_key="gem-test",
                transport=gemini_transport,
            ),
            LLMProviderKind.OLLAMA_VLLM: build_ollama_vllm_provider(
                base_url="http://localhost:11434/v1",
                api_key="local",
                transport=transport,
            ),
        }
    )
    assert gateway.supported_kinds() == {
        LLMProviderKind.OPENAI_COMPATIBLE,
        LLMProviderKind.ANTHROPIC,
        LLMProviderKind.GEMINI,
        LLMProviderKind.OLLAMA_VLLM,
    }
    messages = [LLMMessage(role="user", content="What is torque?")]
    for kind in gateway.supported_kinds():
        result = gateway.complete(
            provider=kind, messages=messages, model_id="m1", temperature=0.0, seed=42
        )
        assert result.text
        assert result.provider == kind
    assert len(gateway.call_log) == 4


def test_all_outbound_calls_go_through_gateway_only() -> None:
    transport = RecordingTransport(response=_openai_response("via-gateway"))
    provider = OpenAICompatibleProvider(
        base_url="https://api.example.com/v1",
        api_key="k",
        transport=transport,
    )
    gateway = LLMEgressGateway(providers={LLMProviderKind.OPENAI_COMPATIBLE: provider})
    out = gateway.complete(
        provider=LLMProviderKind.OPENAI_COMPATIBLE,
        messages=[LLMMessage(role="user", content="hi")],
        model_id="gpt-test",
    )
    assert out.text == "via-gateway"
    assert len(transport.calls) == 1
    assert transport.calls[0]["body"]["temperature"] == 0.0
    assert transport.calls[0]["body"]["seed"] == 42
    with pytest.raises(ValueError, match="provider not registered"):
        gateway.complete(
            provider=LLMProviderKind.ANTHROPIC,
            messages=[LLMMessage(role="user", content="x")],
            model_id="m",
        )
