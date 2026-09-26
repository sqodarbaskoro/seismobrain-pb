"""
File: retrieval_retry.py
Description: Soft-filter retry policy after empty retrieval (FR-RET-10)
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
from typing import Any


@dataclass(frozen=True, slots=True)
class RetrievalAttempt:
    hard_filters: dict[str, Any]
    soft_filters: dict[str, Any]
    hits: int


@dataclass(frozen=True, slots=True)
class RetryPlan:
    should_retry: bool
    drop_soft_filters: bool
    lower_threshold: bool


def plan_retrieval_retry(
    attempt: RetrievalAttempt,
    *,
    model_refused: bool = False,
) -> RetryPlan:
    """No threshold lowering after refusal; one soft-filter retry only if zero hits."""
    if model_refused:
        return RetryPlan(
            should_retry=False, drop_soft_filters=False, lower_threshold=False
        )
    if attempt.hits == 0 and attempt.soft_filters:
        return RetryPlan(
            should_retry=True, drop_soft_filters=True, lower_threshold=False
        )
    return RetryPlan(should_retry=False, drop_soft_filters=False, lower_threshold=False)
