"""
File: research_budgets.py
Description: Hard research-mode budgets with partial answer on exhaustion (FR-AGT-03)
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
class ResearchBudgets:
    sub_queries: int = 4
    llm_calls: int = 4
    retrievals: int = 8
    evidence_items: int = 16
    context_tokens: int = 10_000
    output_tokens: int = 1_500
    wall_clock_s: float = 90.0


@dataclass
class BudgetLedger:
    limits: ResearchBudgets = field(default_factory=ResearchBudgets)
    llm_calls: int = 0
    retrievals: int = 0
    evidence_items: int = 0
    context_tokens: int = 0
    output_tokens: int = 0
    wall_clock_s: float = 0.0
    exhausted: str | None = None

    def charge(
        self,
        *,
        llm: int = 0,
        retrieval: int = 0,
        evidence: int = 0,
        context_tokens: int = 0,
        output_tokens: int = 0,
        wall_s: float = 0.0,
    ) -> bool:
        """Charge usage; return False and set exhausted when a budget is hit."""
        checks = [
            (self.llm_calls + llm > self.limits.llm_calls, "llm_calls"),
            (self.retrievals + retrieval > self.limits.retrievals, "retrievals"),
            (self.evidence_items + evidence > self.limits.evidence_items, "evidence"),
            (
                self.context_tokens + context_tokens > self.limits.context_tokens,
                "context_tokens",
            ),
            (
                self.output_tokens + output_tokens > self.limits.output_tokens,
                "output_tokens",
            ),
            (self.wall_clock_s + wall_s > self.limits.wall_clock_s, "wall_clock"),
        ]
        for over, name in checks:
            if over:
                self.exhausted = name
                return False
        self.llm_calls += llm
        self.retrievals += retrieval
        self.evidence_items += evidence
        self.context_tokens += context_tokens
        self.output_tokens += output_tokens
        self.wall_clock_s += wall_s
        return True


@dataclass(frozen=True, slots=True)
class PartialResearchAnswer:
    text: str
    notice: str
    partial: bool = True


def partial_on_exhaustion(ledger: BudgetLedger, draft: str) -> PartialResearchAnswer:
    reason = ledger.exhausted or "budget"
    return PartialResearchAnswer(
        text=draft,
        notice=f"Research budget exhausted ({reason}); returning partial answer.",
        partial=True,
    )
