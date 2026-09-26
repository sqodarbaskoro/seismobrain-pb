"""
File: test_router_rules.py
Description: FR-QRY-02 — rules-first router; uncertain defaults to doc_qa
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


def test_rules_greeting_and_thanks_before_classifier() -> None:
    assert route_query("hello") == RouteClass.CONVERSATIONAL
    assert route_query("thanks") == RouteClass.CONVERSATIONAL


def test_rules_identifiers_present_force_doc_qa() -> None:
    assert route_query("P2/94") == RouteClass.DOC_QA
    assert route_query("check E-404 please") == RouteClass.DOC_QA


def test_uncertain_defaults_to_doc_qa() -> None:
    assert route_query("can you elaborate") == RouteClass.DOC_QA
    assert route_query("what about the other one") == RouteClass.DOC_QA


def test_classifier_only_used_when_rules_uncertain() -> None:
    calls: list[str] = []

    def classifier(text: str) -> RouteClass | None:
        calls.append(text)
        return RouteClass.OUT_OF_SCOPE

    # Greeting resolved by rules — classifier must not run.
    assert (
        route_query("hello", classifier=classifier) == RouteClass.CONVERSATIONAL
    )
    assert calls == []

    # No rule match — classifier consulted.
    assert route_query("random fluff xyz", classifier=classifier) == RouteClass.OUT_OF_SCOPE
    assert calls == ["random fluff xyz"]


def test_uncertain_classifier_none_defaults_doc_qa() -> None:
    def classifier(_text: str) -> RouteClass | None:
        return None

    assert route_query("ambiguous phrase here", classifier=classifier) == RouteClass.DOC_QA
