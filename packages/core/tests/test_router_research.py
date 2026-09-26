"""
File: test_router_research.py
Description: Router research class when workspace research enabled (T5.30)
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

from seismobrain_core.router import RouteClass, route_query


def test_research_class_when_enabled() -> None:
    q = "compare seal procedure and lockout steps across revisions"
    assert route_query(q, research_enabled=True) == RouteClass.RESEARCH
    # Disabled → falls through to doc_qa via technical cues.
    assert route_query(q, research_enabled=False) == RouteClass.DOC_QA


def test_uncertain_still_doc_qa_with_research_enabled() -> None:
    assert (
        route_query("can you elaborate", research_enabled=True) == RouteClass.DOC_QA
    )
    assert (
        route_query("what about the other one", research_enabled=True)
        == RouteClass.DOC_QA
    )


def test_greeting_unaffected_by_research_flag() -> None:
    assert (
        route_query("hello", research_enabled=True) == RouteClass.CONVERSATIONAL
    )
