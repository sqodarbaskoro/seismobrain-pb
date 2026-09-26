"""
File: query_rewrite.py
Description: Context-dependence check and query rewrite (FR-QRY-04)
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

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from seismobrain_core.identifiers import detect_identifiers, preserve_identifiers

_DEPENDENT = re.compile(
    r"\b("
    r"that|those|this|these|it|they|them|one|same|other|previous|above|"
    r"and\s+the|what\s+about|how\s+about"
    r")\b",
    re.IGNORECASE,
)

RewriterFn = Callable[[str, Sequence[str]], str]

# Procedure follow-ups can omit a subject, including "how can we started?".
_SUBJECTLESS_PROCEDURE = re.compile(
    r"(?:how\s+(?:(?:can|could|do|should|would)\s+(?:i|we|you)\s+|to\s+)?"
    r"|(?:please\s+)?(?:explain|show|give)(?:\s+me)?\s+(?:the\s+)?)"
    r"(?:start(?:ed|ing)?|stop(?:ped|ping)?|restart(?:ed|ing)?|"
    r"install(?:ed|ing)?|configur(?:e|ed|ing)|run(?:ning)?|use|"
    r"steps|procedure|setup)(?:\s+(?:please|again))?[?.!]*",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class RewriteResult:
    query: str
    rewritten: bool


def is_context_dependent(question: str) -> bool:
    """True when the question likely needs prior-turn context to stand alone."""
    text = question.strip()
    if len(text.split()) <= 6 and _DEPENDENT.search(text):
        return True
    if text.lower().startswith(("what about", "how about", "and the", "the same")):
        return True
    if _SUBJECTLESS_PROCEDURE.fullmatch(text):
        return True
    return False


def _active_history(history: Sequence[str]) -> tuple[str, ...]:
    """Keep the latest standalone topic plus recent dependent turns.

    Raw user turns are stored verbatim, so the last turn alone may be another
    unresolved follow-up. Keep its topic anchor even across a long chain, and
    stop at a new standalone question so earlier topics do not leak into it.
    """
    turns = [turn for turn in history if turn.strip()]
    for index in range(len(turns) - 1, -1, -1):
        if not is_context_dependent(turns[index]):
            return (turns[index], *turns[max(index + 1, len(turns) - 3):])
    return tuple(turns[-4:])


def maybe_rewrite(
    question: str,
    *,
    history: Sequence[str] = (),
    rewriter: RewriterFn | None = None,
) -> RewriteResult:
    """Rewrite only context-dependent follow-ups using a small fast model hook."""
    if not is_context_dependent(question) or not history:
        return RewriteResult(query=question, rewritten=False)
    context = _active_history(history)
    if not context:
        return RewriteResult(query=question, rewritten=False)
    if rewriter is None:
        rewritten = f"{question} (context: {'; '.join(context)})"
    else:
        rewritten = rewriter(question, context)
    return RewriteResult(query=rewritten, rewritten=True)


def guarded_rewrite(
    question: str,
    *,
    history: Sequence[str] = (),
    rewriter: RewriterFn | None = None,
) -> RewriteResult:
    """Discard rewrites that drop identifiers from the question or active topic."""
    context = _active_history(history)
    ids = detect_identifiers(question)
    for turn in context:
        for token in detect_identifiers(turn):
            if token not in ids:
                ids.append(token)

    if rewriter is not None:
        candidate = RewriteResult(query=rewriter(question, context), rewritten=True)
    else:
        candidate = maybe_rewrite(question, history=context)

    if not candidate.rewritten:
        return candidate
    kept = preserve_identifiers(question, candidate.query, ids)
    if kept != candidate.query:
        return RewriteResult(query=question, rewritten=False)
    return candidate
