"""
File: analytics.py
Description: Admin analytics aggregates (FR-ADM-08)
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

from collections import Counter
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AnalyticsStore:
    usage_events: list[dict[str, Any]] = field(default_factory=list)
    refusals: list[str] = field(default_factory=list)
    latencies_ms: list[float] = field(default_factory=list)
    unanswered: list[str] = field(default_factory=list)
    feedback: list[dict[str, str]] = field(default_factory=list)

    def record_usage(self, *, route: str, workspace_id: str) -> None:
        self.usage_events.append({"route": route, "workspace_id": workspace_id})

    def record_refusal(self, refusal_type: str) -> None:
        self.refusals.append(refusal_type)

    def record_latency(self, ms: float) -> None:
        self.latencies_ms.append(ms)

    def record_unanswered(self, question: str) -> None:
        self.unanswered.append(question)

    def record_feedback(self, *, rating: str, reason: str) -> None:
        self.feedback.append({"rating": rating, "reason": reason})

    def snapshot(self) -> dict[str, Any]:
        lat = sorted(self.latencies_ms)
        p95 = lat[int(0.95 * (len(lat) - 1))] if lat else 0.0
        top_unanswered = [
            {"question": q, "count": c}
            for q, c in Counter(self.unanswered).most_common(10)
        ]
        return {
            "usage": {
                "total": len(self.usage_events),
                "by_route": dict(Counter(e["route"] for e in self.usage_events)),
            },
            "refusal_mix": dict(Counter(self.refusals)),
            "latency": {"p95_ms": p95, "samples": len(lat)},
            "top_unanswered_questions": top_unanswered,
            "feedback_trends": {
                "by_rating": dict(Counter(f["rating"] for f in self.feedback)),
                "by_reason": dict(Counter(f["reason"] for f in self.feedback)),
            },
        }
