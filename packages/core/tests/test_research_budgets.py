"""
File: test_research_budgets.py
Description: Research hard budgets with partial answer (T5.3)
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

from seismobrain_core.research_budgets import (
    BudgetLedger,
    ResearchBudgets,
    partial_on_exhaustion,
)


def test_budget_exhaustion_returns_partial_with_notice() -> None:
    ledger = BudgetLedger(limits=ResearchBudgets(llm_calls=2, retrievals=2))
    assert ledger.charge(llm=1) is True
    assert ledger.charge(llm=1) is True
    assert ledger.charge(llm=1) is False
    assert ledger.exhausted == "llm_calls"
    partial = partial_on_exhaustion(ledger, draft="Partial findings [E1].")
    assert partial.partial is True
    assert "budget exhausted" in partial.notice.lower()
    assert "Partial findings" in partial.text
