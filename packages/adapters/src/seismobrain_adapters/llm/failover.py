"""
File: failover.py
Description: Secondary LLM provider failover via egress gateway (NFR-REL-05)
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

from seismobrain_adapters.llm.gateway import EgressBlockedError, LLMEgressGateway
from seismobrain_core.ports.llm_provider import LLMCompletion, LLMMessage, LLMProviderKind


@dataclass
class FailoverLLMGateway:
    gateway: LLMEgressGateway
    primary: LLMProviderKind
    secondary: LLMProviderKind | None
    primary_model: str
    secondary_model: str | None = None

    def complete(self, *, messages: Sequence[LLMMessage]) -> LLMCompletion:
        try:
            return self.gateway.complete(
                provider=self.primary,
                messages=messages,
                model_id=self.primary_model,
            )
        except EgressBlockedError:
            raise
        except Exception:
            if self.secondary is None or self.secondary_model is None:
                raise
            return self.gateway.complete(
                provider=self.secondary,
                messages=messages,
                model_id=self.secondary_model,
            )
