"""
File: test_retrieval_metrics.py
Description: Retrieval metrics sliced by query type (T2.22)
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

from seismobrain_eval.metrics import RankedCase, aggregate_recall_at_k, recall_at_k


def test_recall_at_k_and_slices() -> None:
    assert recall_at_k(["a", "b", "c"], ["a", "z"], k=10) == 0.5
    cases = [
        RankedCase("1", "identifier", "ops", "easy", ["a", "b"], ["a"]),
        RankedCase("2", "procedural", "ops", "medium", ["x", "y"], ["z"]),
        RankedCase("3", "identifier", "safety", "easy", ["p"], ["p"]),
    ]
    metrics = aggregate_recall_at_k(cases, k=10)
    assert metrics["all"] == sum([1.0, 0.0, 1.0]) / 3
    assert metrics["identifier"] == 1.0
    assert metrics["query_type:procedural"] == 0.0
    assert "collection:ops" in metrics
    assert "difficulty:easy" in metrics
