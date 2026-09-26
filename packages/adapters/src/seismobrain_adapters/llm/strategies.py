"""
File: strategies.py
Description: OpenAI-compatible, Anthropic, Gemini, Ollama/vLLM LLM strategies
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
from typing import Any

from seismobrain_adapters.llm.transport import JsonHttpTransport
from seismobrain_core.ports.llm_provider import (
    LLMCompletion,
    LLMMessage,
    LLMProviderKind,
)


def _msg_dicts(messages: Sequence[LLMMessage]) -> list[dict[str, str]]:
    return [{"role": m.role, "content": m.content} for m in messages]


class OpenAICompatibleProvider:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        transport: JsonHttpTransport,
        kind: LLMProviderKind = LLMProviderKind.OPENAI_COMPATIBLE,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._transport = transport
        self._kind = kind

    @property
    def kind(self) -> LLMProviderKind:
        return self._kind

    def complete(
        self,
        messages: Sequence[LLMMessage],
        *,
        model_id: str,
        temperature: float = 0.0,
        seed: int | None = 42,
        max_tokens: int = 1024,
    ) -> LLMCompletion:
        body: dict[str, Any] = {
            "model": model_id,
            "messages": _msg_dicts(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if seed is not None:
            body["seed"] = seed
        data = self._transport.post_json(
            f"{self._base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self._api_key}"},
            body=body,
        )
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return LLMCompletion(
            text=text,
            provider=self._kind,
            model_id=model_id,
            tokens_in=int(usage.get("prompt_tokens", 0)),
            tokens_out=int(usage.get("completion_tokens", 0)),
        )


class AnthropicProvider:
    def __init__(
        self, *, base_url: str, api_key: str, transport: JsonHttpTransport
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._transport = transport

    @property
    def kind(self) -> LLMProviderKind:
        return LLMProviderKind.ANTHROPIC

    def complete(
        self,
        messages: Sequence[LLMMessage],
        *,
        model_id: str,
        temperature: float = 0.0,
        seed: int | None = 42,
        max_tokens: int = 1024,
    ) -> LLMCompletion:
        _ = seed  # Anthropic may ignore seed; gateway still passes it.
        system = "\n".join(m.content for m in messages if m.role == "system")
        user_msgs = [m for m in messages if m.role != "system"]
        body: dict[str, Any] = {
            "model": model_id,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": _msg_dicts(user_msgs),
        }
        if system:
            body["system"] = system
        data = self._transport.post_json(
            f"{self._base_url}/v1/messages",
            headers={
                "x-api-key": self._api_key,
                "anthropic-version": "2023-06-01",
            },
            body=body,
        )
        text = "".join(
            block.get("text", "")
            for block in data.get("content", [])
            if block.get("type") == "text"
        )
        usage = data.get("usage", {})
        return LLMCompletion(
            text=text,
            provider=LLMProviderKind.ANTHROPIC,
            model_id=model_id,
            tokens_in=int(usage.get("input_tokens", 0)),
            tokens_out=int(usage.get("output_tokens", 0)),
        )


class GeminiProvider:
    def __init__(
        self, *, base_url: str, api_key: str, transport: JsonHttpTransport
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._transport = transport

    @property
    def kind(self) -> LLMProviderKind:
        return LLMProviderKind.GEMINI

    def complete(
        self,
        messages: Sequence[LLMMessage],
        *,
        model_id: str,
        temperature: float = 0.0,
        seed: int | None = 42,
        max_tokens: int = 1024,
    ) -> LLMCompletion:
        contents = []
        for msg in messages:
            role = "user" if msg.role == "user" else "model"
            if msg.role == "system":
                role = "user"
            contents.append({"role": role, "parts": [{"text": msg.content}]})
        body: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if seed is not None:
            body["generationConfig"]["seed"] = seed
        url = (
            f"{self._base_url}/v1beta/models/{model_id}:generateContent"
            f"?key={self._api_key}"
        )
        data = self._transport.post_json(url, headers={}, body=body)
        candidates = data.get("candidates", [])
        text = ""
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            text = "".join(p.get("text", "") for p in parts)
        return LLMCompletion(
            text=text,
            provider=LLMProviderKind.GEMINI,
            model_id=model_id,
            tokens_in=0,
            tokens_out=0,
        )


def build_ollama_vllm_provider(
    *, base_url: str, api_key: str, transport: JsonHttpTransport
) -> OpenAICompatibleProvider:
    """Ollama/vLLM speak OpenAI chat completions; tagged as local kind for egress."""
    return OpenAICompatibleProvider(
        base_url=base_url,
        api_key=api_key or "local",
        transport=transport,
        kind=LLMProviderKind.OLLAMA_VLLM,
    )
