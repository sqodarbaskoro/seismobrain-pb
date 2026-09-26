"""
File: test_query_rewrite.py
Description: FR-QRY-04 — context-dependence check and rewrite
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-19
Version: 0.1.1
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

import pytest

from seismobrain_core.query_rewrite import (
    RewriteResult,
    guarded_rewrite,
    is_context_dependent,
    maybe_rewrite,
)


def test_standalone_question_not_rewritten() -> None:
    result = maybe_rewrite(
        "What is the torque for flange P2/94?",
        history=("Earlier we discussed pumps.",),
    )
    assert result.rewritten is False
    assert result.query == "What is the torque for flange P2/94?"


def test_follow_up_with_pronoun_is_context_dependent() -> None:
    assert is_context_dependent("What about that one?") is True
    assert is_context_dependent("And the revision?") is True
    assert is_context_dependent("What is the torque for flange P2/94?") is False


def test_dependent_follow_up_rewritten_with_history() -> None:
    result = maybe_rewrite(
        "What about that one?",
        history=("We were reviewing flange P2/94.",),
        rewriter=lambda q, h: f"{q} regarding flange P2/94",
    )
    assert result.rewritten is True
    assert "P2/94" in result.query
    assert isinstance(result, RewriteResult)


@pytest.mark.parametrize("topic", ["synckit", "SYNCKIT"])
@pytest.mark.parametrize(
    "question",
    ["how can we started?", "How do I start?", "Show me the steps.", "How does it work?"],
)
def test_followup_chain_keeps_original_topic(topic: str, question: str) -> None:
    result = guarded_rewrite(
        question, history=(f"what is {topic}", "where this is started?")
    )
    assert result.rewritten
    assert topic in result.query
    assert result.query.startswith(question)


def test_long_followup_chain_keeps_anchor_without_unbounded_history() -> None:
    result = guarded_rewrite(
        "How do I start?", history=("What is SYNCKIT?", *("How does it work?",) * 20)
    )
    assert result.rewritten
    assert "SYNCKIT" in result.query
    assert result.query.count("How does it work?") <= 3


def test_topic_switch_does_not_require_identifiers_from_old_topic() -> None:
    history = ("What is SYNCKIT?", "Where is it started?", "What is Route-Guide?")
    result = guarded_rewrite("How do I start?", history=history)
    assert result.rewritten
    assert "Route-Guide" in result.query
    assert "SYNCKIT" not in result.query


@pytest.mark.parametrize("question", ["How do I start Route-Guide?", "What is OPSCONSOLE GPS?"])
def test_explicit_new_question_stays_standalone(question: str) -> None:
    result = guarded_rewrite(question, history=("What is SYNCKIT?", "Where is it started?"))
    assert not result.rewritten
    assert result.query == question


def test_subjectless_question_without_history_is_unchanged() -> None:
    result = guarded_rewrite("how can we started?")
    assert not result.rewritten


def test_rewrite_cannot_drop_active_topic_identifier() -> None:
    result = guarded_rewrite(
        "How does it work?",
        history=("What is SYNCKIT?", "Where is it started?"),
        rewriter=lambda q, h: "How does the system work?",
    )
    assert not result.rewritten
