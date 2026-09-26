"""
File: egress_policy.py
Description: Workspace and deployment data-egress policies (FR-ADM-06)
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
from dataclasses import dataclass, field
from enum import StrEnum

from seismobrain_core.ports.llm_provider import LLMProviderKind

LOCAL_KINDS = frozenset({LLMProviderKind.OLLAMA_VLLM})


class EgressPolicy(StrEnum):
    OPEN = "open"
    APPROVED_PROVIDERS = "approved_providers"
    LOCAL_ONLY = "local_only"


@dataclass(frozen=True, slots=True)
class ApprovedProvider:
    kind: LLMProviderKind
    model_id: str


@dataclass(frozen=True, slots=True)
class EgressDecision:
    allowed: bool
    reason: str


@dataclass
class EgressAuditLog:
    entries: list[dict[str, object]] = field(default_factory=list)

    def record_blocked(
        self,
        *,
        provider: LLMProviderKind,
        model_id: str,
        policy: EgressPolicy,
        reason: str,
    ) -> None:
        self.entries.append(
            {
                "event": "egress_blocked",
                "provider": provider.value,
                "model_id": model_id,
                "policy": policy.value,
                "reason": reason,
            }
        )


def decide_egress(
    *,
    policy: EgressPolicy,
    provider: LLMProviderKind,
    model_id: str,
    approved: Sequence[ApprovedProvider] = (),
    air_gapped: bool = False,
) -> EgressDecision:
    effective = EgressPolicy.LOCAL_ONLY if air_gapped else policy
    if effective is EgressPolicy.OPEN:
        return EgressDecision(allowed=True, reason="open")
    if effective is EgressPolicy.LOCAL_ONLY:
        if provider in LOCAL_KINDS:
            return EgressDecision(allowed=True, reason="local_provider")
        return EgressDecision(allowed=False, reason="local_only_blocks_external")
    # approved_providers
    for item in approved:
        if item.kind is provider and item.model_id == model_id:
            return EgressDecision(allowed=True, reason="approved")
    return EgressDecision(allowed=False, reason="provider_not_approved")
