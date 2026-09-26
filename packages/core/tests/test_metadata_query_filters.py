"""
File: test_metadata_query_filters.py
Description: Explicit hard filter vs inferred soft boost (T4.14)
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

from seismobrain_core.metadata_query_filters import plan_metadata_filters


def test_explicit_hard_inferred_soft() -> None:
    plan = plan_metadata_filters(
        "doc_type:pdf author:alice torque for this pump"
    )
    assert plan.hard_filters["doc_type"] == "pdf"
    assert plan.hard_filters["author"] == "alice"
    assert "doc_type" not in plan.soft_boosts

    soft_only = plan_metadata_filters("english procedure for pumps")
    assert soft_only.hard_filters == {}
    assert soft_only.soft_boosts["doc_type"] == "procedure"
    assert soft_only.soft_boosts["language"] == "english"
