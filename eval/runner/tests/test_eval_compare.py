"""
File: test_eval_compare.py
Description: Eval run comparison with per-case differences (T5.33)
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

from seismobrain_eval.compare import CaseResult, compare_runs


def test_eval_compare_per_case_differences() -> None:
    baseline = [
        CaseResult("1", 1.0, ("a", "b")),
        CaseResult("2", 0.5, ("x", "y")),
        CaseResult("3", 1.0, ("p",)),
    ]
    candidate = [
        CaseResult("1", 1.0, ("a", "b")),
        CaseResult("2", 1.0, ("y", "x")),
        CaseResult("3", 0.0, ("q",)),
    ]
    report = compare_runs(baseline, candidate, baseline_run="r1", candidate_run="r2")
    assert len(report.diffs) == 3
    by_id = {d.case_id: d for d in report.diffs}
    assert by_id["1"].delta == 0.0
    assert by_id["1"].changed_ranking is False
    assert by_id["2"].delta == 0.5
    assert by_id["2"].changed_ranking is True
    assert by_id["3"].delta == -1.0
    assert len(report.improvements) == 1
    assert len(report.regressions) == 1
    assert report.regressions[0].case_id == "3"
