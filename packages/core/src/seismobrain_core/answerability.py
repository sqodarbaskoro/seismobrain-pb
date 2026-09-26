"""
File: answerability.py
Description: Heuristic query-level answerability gate (FR-RET-05)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-17
Version: 0.2.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EvidenceSnippet:
    text: str
    relevance: float


@dataclass(frozen=True, slots=True)
class GateDecision:
    answerable: bool
    reason: str


_TOKEN = re.compile(r"[a-z0-9]+", re.IGNORECASE)
_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "of",
        "to",
        "in",
        "on",
        "for",
        "is",
        "are",
        "was",
        "were",
        "be",
        "my",
        "our",
        "your",
        "what",
        "whats",
        "which",
        "who",
        "how",
        "when",
        "where",
        "why",
        "does",
        "do",
        "did",
        "can",
        "could",
        "would",
        "should",
        "about",
        "with",
        "from",
        "into",
        "this",
        "that",
        "these",
        "those",
        "me",
        "we",
        "you",
        "it",
        "its",
        "please",
        "tell",
        "show",
        "give",
        "list",
        "document",
        "documents",
        "doc",
        "docs",
        "file",
        "files",
        "content",
        "contents",
        "there",
        "here",
        "any",
        "some",
        "all",
    }
)


def _content_tokens(text: str) -> set[str]:
    return {
        t
        for t in _TOKEN.findall(text.lower())
        if len(t) > 2 and t not in _STOPWORDS
    }


def heuristic_answerability(
    query: str,
    evidence: Sequence[EvidenceSnippet],
    *,
    min_overlap: float = 0.25,
    min_relevance: float = 0.1,
) -> GateDecision:
    """Decide whether selected evidence can answer; no raw similarity threshold alone."""
    if not evidence:
        return GateDecision(answerable=False, reason="no_evidence")
    q_tokens = _content_tokens(query)
    # Inventory / meta questions ("what's in my documents?") have no content tokens
    # left after stopword stripping — allow generation over the scoped evidence.
    if not q_tokens:
        return GateDecision(answerable=True, reason="scoped_inventory")
    best_overlap = 0.0
    best_rel = 0.0
    for item in evidence:
        e_tokens = set(_TOKEN.findall(item.text.lower()))
        if not e_tokens:
            continue
        overlap = len(q_tokens & e_tokens) / len(q_tokens)
        best_overlap = max(best_overlap, overlap)
        best_rel = max(best_rel, item.relevance)
    if best_overlap >= min_overlap and best_rel >= min_relevance:
        return GateDecision(answerable=True, reason="overlap_and_relevance")
    if best_overlap >= min_overlap:
        return GateDecision(answerable=True, reason="lexical_overlap")
    return GateDecision(answerable=False, reason="insufficient_evidence")
