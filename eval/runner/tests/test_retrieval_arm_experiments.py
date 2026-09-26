"""
File: test_retrieval_arm_experiments.py
Description: Retrieval-only arm ablation experiments (T2.25)
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

from seismobrain_eval.experiments import run_arm_ablation


def test_arm_ablation_covers_required_arms() -> None:
    arms = run_arm_ablation()
    for key in ("dense", "bm25_text", "ident", "fused", "reranked"):
        assert key in arms
        assert len(arms[key]) >= 1
    assert set(arms["fused"]).issuperset({"a", "b", "c"})
