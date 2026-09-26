"""
File: test_router_p0.py
Description: FR-QRY-01 — router classes doc_qa / conversational / out_of_scope
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

# Technical / document questions — must never land on conversational.
_TECHNICAL = (
    "What is the torque spec for flange P2/94?",
    "How do I reset error E-404 on the pump controller?",
    "Compare revision B and C of the HSE procedure",
    "Where is the lockout procedure for well-alpha-12?",
    "What does section 4.2 of the pump manual say about seals?",
    "List the PPE required before servicing CP-100",
    "Explain the difference between isolation and lockout",
    "What is the host address for telemetry on 10.0.0.15?",
)

_CONVERSATIONAL = (
    "hello",
    "Hi there!",
    "thanks",
    "Thank you so much",
    "good morning",
)

_OUT_OF_SCOPE = (
    "What's the weather in Singapore today?",
    "Write me a poem about cats",
    "Who won the world cup in 2018?",
)


def test_router_classes_are_defined() -> None:
    assert set(RouteClass) >= {
        RouteClass.DOC_QA,
        RouteClass.CONVERSATIONAL,
        RouteClass.OUT_OF_SCOPE,
    }


def test_technical_questions_never_misrouted_to_conversational() -> None:
    misrouted = [
        q for q in _TECHNICAL if route_query(q) == RouteClass.CONVERSATIONAL
    ]
    assert misrouted == [], f"technical misrouted to conversational: {misrouted}"


def test_technical_questions_route_to_doc_qa() -> None:
    for q in _TECHNICAL:
        assert route_query(q) == RouteClass.DOC_QA, q


def test_greetings_route_to_conversational() -> None:
    for q in _CONVERSATIONAL:
        assert route_query(q) == RouteClass.CONVERSATIONAL, q


def test_clearly_off_topic_routes_out_of_scope() -> None:
    for q in _OUT_OF_SCOPE:
        assert route_query(q) == RouteClass.OUT_OF_SCOPE, q


def test_default_uncertain_is_doc_qa() -> None:
    assert route_query("tell me more about that") == RouteClass.DOC_QA
