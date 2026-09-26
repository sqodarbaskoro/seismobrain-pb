"""
File: provider_test.py
Description: Build LLM strategy and run a connection probe for admin provider test
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-17
Modified: 2026-09-17
Version: 0.1.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

from seismobrain_adapters.llm.strategies import (
    AnthropicProvider,
    GeminiProvider,
    OpenAICompatibleProvider,
    build_ollama_vllm_provider,
)
from seismobrain_adapters.llm.transport import JsonHttpTransport
from seismobrain_api.admin_catalog import ProviderRecord
from seismobrain_core.ports.llm_provider import LLMMessage, LLMProviderKind


def build_strategy(
    *,
    kind: str,
    base_url: str,
    api_key: str,
    transport: JsonHttpTransport,
) -> OpenAICompatibleProvider | AnthropicProvider | GeminiProvider:
    if kind == LLMProviderKind.OPENAI_COMPATIBLE.value:
        return OpenAICompatibleProvider(
            base_url=base_url, api_key=api_key, transport=transport
        )
    if kind == LLMProviderKind.ANTHROPIC.value:
        return AnthropicProvider(
            base_url=base_url, api_key=api_key, transport=transport
        )
    if kind == LLMProviderKind.GEMINI.value:
        return GeminiProvider(base_url=base_url, api_key=api_key, transport=transport)
    if kind == LLMProviderKind.OLLAMA_VLLM.value:
        return build_ollama_vllm_provider(
            base_url=base_url, api_key=api_key, transport=transport
        )
    raise ValueError(f"unsupported provider kind: {kind}")


def probe_provider(
    record: ProviderRecord,
    *,
    api_key: str,
    transport: JsonHttpTransport,
) -> dict[str, object]:
    """Run a minimal completion against the configured provider."""
    if not record.models:
        return {"ok": False, "error": "no models configured"}
    if not record.base_url:
        return {"ok": False, "error": "base_url required"}
    try:
        strategy = build_strategy(
            kind=record.kind,
            base_url=record.base_url,
            api_key=api_key,
            transport=transport,
        )
        strategy.complete(
            [LLMMessage(role="user", content="ping")],
            model_id=record.models[0],
            temperature=0.0,
            seed=42,
            max_tokens=8,
        )
    except Exception as exc:  # noqa: BLE001 — surface connection errors to admin UI
        return {"ok": False, "error": str(exc)}
    return {"ok": True}
