"""
File: typed_refusals.py
Description: Typed refusal messages (FR-GEN-08)
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

from dataclasses import dataclass
from enum import StrEnum


class RefusalType(StrEnum):
    NO_EVIDENCE = "no_evidence"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    OUT_OF_SCOPE = "out_of_scope"
    POLICY_BLOCKED = "policy_blocked"
    PROVIDER_ERROR = "provider_error"


_MESSAGES: dict[RefusalType, str] = {
    RefusalType.NO_EVIDENCE: (
        "Nothing in scope matches this question. Try broadening collections or filters."
    ),
    RefusalType.INSUFFICIENT_EVIDENCE: (
        "Related material exists but does not fully answer the question."
    ),
    RefusalType.OUT_OF_SCOPE: (
        "This does not appear to be a question about your documents."
    ),
    RefusalType.POLICY_BLOCKED: (
        "A workspace or deployment policy blocked this request."
    ),
    RefusalType.PROVIDER_ERROR: (
        "The language model failed temporarily. Please retry."
    ),
}


@dataclass(frozen=True, slots=True)
class Refusal:
    type: RefusalType
    message: str
    policy_name: str | None = None


def make_refusal(
    refusal_type: RefusalType, *, policy_name: str | None = None
) -> Refusal:
    message = _MESSAGES[refusal_type]
    if refusal_type is RefusalType.POLICY_BLOCKED and policy_name:
        message = f"Blocked by policy: {policy_name}."
    return Refusal(type=refusal_type, message=message, policy_name=policy_name)


def distinct_messages() -> dict[str, str]:
    return {t.value: _MESSAGES[t] for t in RefusalType}
