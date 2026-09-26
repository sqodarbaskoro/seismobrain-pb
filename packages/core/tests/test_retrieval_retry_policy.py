"""
File: test_retrieval_retry_policy.py
Description: FR-RET-10 — no threshold lowering; one soft-filter retry
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

from seismobrain_core.retrieval_retry import RetrievalAttempt, plan_retrieval_retry


def test_zero_hits_retries_without_soft_filters() -> None:
    plan = plan_retrieval_retry(
        RetrievalAttempt(
            hard_filters={"tenant_id": "t1"},
            soft_filters={"inferred_doc_type": "pdf"},
            hits=0,
        )
    )
    assert plan.should_retry is True
    assert plan.drop_soft_filters is True
    assert plan.lower_threshold is False


def test_refusal_does_not_lower_threshold() -> None:
    plan = plan_retrieval_retry(
        RetrievalAttempt(hard_filters={}, soft_filters={"x": 1}, hits=0),
        model_refused=True,
    )
    assert plan.should_retry is False
    assert plan.lower_threshold is False


def test_nonzero_hits_no_retry() -> None:
    plan = plan_retrieval_retry(
        RetrievalAttempt(hard_filters={}, soft_filters={"x": 1}, hits=3)
    )
    assert plan.should_retry is False
