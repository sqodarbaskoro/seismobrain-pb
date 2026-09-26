"""
File: gateway.py
Description: Single egress LLM gateway — only outbound path for providers (SEC-13)
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

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from seismobrain_core.egress_policy import (
    ApprovedProvider,
    EgressAuditLog,
    EgressPolicy,
    decide_egress,
)
from seismobrain_core.ports.llm_provider import (
    LLMCompletion,
    LLMMessage,
    LLMProvider,
    LLMProviderKind,
)


class EgressBlockedError(PermissionError):
    """Raised when workspace/deployment egress policy blocks a provider call."""


@dataclass
class LLMEgressGateway:
    """All outbound LLM calls MUST go through this gateway."""

    providers: Mapping[LLMProviderKind, LLMProvider]
    call_log: list[dict[str, object]] = field(default_factory=list)
    policy: EgressPolicy = EgressPolicy.OPEN
    approved: tuple[ApprovedProvider, ...] = ()
    air_gapped: bool = False
    audit: EgressAuditLog = field(default_factory=EgressAuditLog)

    def supported_kinds(self) -> set[LLMProviderKind]:
        return set(self.providers.keys())

    def complete(
        self,
        *,
        provider: LLMProviderKind,
        messages: Sequence[LLMMessage],
        model_id: str,
        temperature: float = 0.0,
        seed: int | None = 42,
        max_tokens: int = 1024,
    ) -> LLMCompletion:
        decision = decide_egress(
            policy=self.policy,
            provider=provider,
            model_id=model_id,
            approved=self.approved,
            air_gapped=self.air_gapped,
        )
        if not decision.allowed:
            self.audit.record_blocked(
                provider=provider,
                model_id=model_id,
                policy=EgressPolicy.LOCAL_ONLY if self.air_gapped else self.policy,
                reason=decision.reason,
            )
            raise EgressBlockedError(decision.reason)
        strategy = self.providers.get(provider)
        if strategy is None:
            raise ValueError(f"provider not registered: {provider}")
        result = strategy.complete(
            messages,
            model_id=model_id,
            temperature=temperature,
            seed=seed,
            max_tokens=max_tokens,
        )
        self.call_log.append(
            {
                "provider": provider.value,
                "model_id": model_id,
                "temperature": temperature,
                "seed": seed,
                "max_tokens": max_tokens,
            }
        )
        return result
