"""
File: llm_provider.py
Description: LLMProvider port — completion strategies (FR-ADM-04)
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
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class LLMProviderKind(StrEnum):
    OPENAI_COMPATIBLE = "openai_compatible"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OLLAMA_VLLM = "ollama_vllm"


@dataclass(frozen=True, slots=True)
class LLMMessage:
    role: str
    content: str


@dataclass(frozen=True, slots=True)
class LLMCompletion:
    text: str
    provider: LLMProviderKind
    model_id: str
    tokens_in: int = 0
    tokens_out: int = 0


class LLMProvider(Protocol):
    """Provider strategy for a single LLM backend family."""

    @property
    def kind(self) -> LLMProviderKind:
        """Return which strategy this implementation serves."""

    def complete(
        self,
        messages: Sequence[LLMMessage],
        *,
        model_id: str,
        temperature: float = 0.0,
        seed: int | None = 42,
        max_tokens: int = 1024,
    ) -> LLMCompletion:
        """Run a chat completion against this provider."""
