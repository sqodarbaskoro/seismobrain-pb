"""
File: metrics.py
Description: Retrieval metrics sliced by query type (FR-EVAL-03)
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

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RankedCase:
    case_id: str
    query_type: str
    collection: str
    difficulty: str
    ranked_ids: Sequence[str]
    relevant_ids: Sequence[str]


def recall_at_k(ranked: Sequence[str], relevant: Sequence[str], *, k: int) -> float:
    if not relevant:
        return 0.0
    hit = len(set(ranked[:k]) & set(relevant))
    return hit / len(set(relevant))


def aggregate_recall_at_k(
    cases: Sequence[RankedCase], *, k: int = 10
) -> dict[str, float]:
    """Overall and sliced recall@k by query_type / collection / difficulty."""
    buckets: dict[str, list[float]] = defaultdict(list)
    for case in cases:
        score = recall_at_k(case.ranked_ids, case.relevant_ids, k=k)
        buckets["all"].append(score)
        buckets[f"query_type:{case.query_type}"].append(score)
        buckets[f"collection:{case.collection}"].append(score)
        buckets[f"difficulty:{case.difficulty}"].append(score)
        if case.query_type == "identifier":
            buckets["identifier"].append(score)
    return {key: (sum(vals) / len(vals) if vals else 0.0) for key, vals in buckets.items()}
