"""
File: test_eval_runner_path.py
Description: Eval runner production path and entitlements (T2.21)
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

import pytest

from seismobrain_eval.dataset_io import EvalCase, EvalDataset
from seismobrain_eval.runner import run_evaluation


def test_runner_requires_eval_read_entitlement() -> None:
    dataset = EvalDataset(
        name="x",
        version="0",
        cases=[EvalCase("1", "q", "factual", ["a"])],
    )
    with pytest.raises(PermissionError):
        run_evaluation(dataset, retrieve=lambda c: list(c.relevant_ids), entitlements=())


def test_runner_uses_production_pipeline_path() -> None:
    dataset = EvalDataset(
        name="x",
        version="0",
        cases=[EvalCase("1", "q", "factual", ["a"])],
    )
    record = run_evaluation(
        dataset,
        retrieve=lambda c: list(c.relevant_ids),
        config={"pipeline": "production"},
        service_principal="eval-runner",
    )
    assert record.used_production_path is True
    assert record.service_principal == "eval-runner"
