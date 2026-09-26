"""
File: compare.py
Description: Eval run comparison with per-case differences (FR-EVAL-05)
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

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class CaseResult:
    case_id: str
    recall_at_10: float
    ranked_ids: tuple[str, ...] = ()


@dataclass
class CaseDiff:
    case_id: str
    baseline_recall: float
    candidate_recall: float
    delta: float
    changed_ranking: bool


@dataclass
class CompareReport:
    baseline_run: str
    candidate_run: str
    diffs: list[CaseDiff] = field(default_factory=list)

    @property
    def regressions(self) -> list[CaseDiff]:
        return [d for d in self.diffs if d.delta < 0]

    @property
    def improvements(self) -> list[CaseDiff]:
        return [d for d in self.diffs if d.delta > 0]


def compare_runs(
    baseline: list[CaseResult],
    candidate: list[CaseResult],
    *,
    baseline_run: str = "baseline",
    candidate_run: str = "candidate",
) -> CompareReport:
    by_id = {c.case_id: c for c in candidate}
    diffs: list[CaseDiff] = []
    for b in baseline:
        c = by_id.get(b.case_id)
        if c is None:
            continue
        diffs.append(
            CaseDiff(
                case_id=b.case_id,
                baseline_recall=b.recall_at_10,
                candidate_recall=c.recall_at_10,
                delta=c.recall_at_10 - b.recall_at_10,
                changed_ranking=b.ranked_ids != c.ranked_ids,
            )
        )
    return CompareReport(
        baseline_run=baseline_run,
        candidate_run=candidate_run,
        diffs=diffs,
    )
