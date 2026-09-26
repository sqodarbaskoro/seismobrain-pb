"""
File: router.py
Description: Query router — doc_qa / conversational / out_of_scope (FR-QRY-01/02)
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
from collections.abc import Callable
from enum import StrEnum

ClassifierFn = Callable[[str], "RouteClass | None"]


class RouteClass(StrEnum):
    DOC_QA = "doc_qa"
    CONVERSATIONAL = "conversational"
    OUT_OF_SCOPE = "out_of_scope"
    RESEARCH = "research"


_GREETING = re.compile(
    r"^\s*(hi|hello|hey|howdy|good\s+(morning|afternoon|evening)|yo)"
    r"(\s+there)?[\s!.?]*$",
    re.IGNORECASE,
)
_THANKS = re.compile(
    r"^\s*(thanks|thank\s+you|thx|ty|cheers)([\s!,.]*|[\s]+so\s+much[!.,]*)?\s*$",
    re.IGNORECASE,
)
# Machine identifiers / technical markers → always doc_qa (never conversational).
_HAS_IDENTIFIER = re.compile(
    r"("
    r"[A-Za-z0-9]+(?:[_\-/.:][A-Za-z0-9]+)+"  # compound ids
    r"|\b[A-Z]{2,}\b"  # acronyms
    r"|\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
    r"|\b[A-Za-z]-?\d{2,}\b"  # E-404 style
    r")"
)
_TECHNICAL_CUE = re.compile(
    r"\b("
    r"how\s+do\s+i|what\s+is|what\s+does|where\s+is|compare|explain|list|"
    r"procedure|manual|section|revision|torque|spec|seal|ppe|lockout|"
    r"isolation|pump|flange|controller|telemetry|host|error|code|"
    r"document|according\s+to|per\s+the"
    r")\b",
    re.IGNORECASE,
)
_OUT_OF_SCOPE = re.compile(
    r"\b("
    r"weather|forecast|poem|joke|song|recipe|sports?|world\s+cup|"
    r"stock\s+price|cryptocurrency|horoscope|celebrity"
    r")\b",
    re.IGNORECASE,
)
# Multi-hop / synthesis cues → research when workspace research is enabled.
_RESEARCH_CUE = re.compile(
    r"\b("
    r"compare|contrast|across|synthesize|summarise|summarize|"
    r"trade-?offs?|versus|vs\.?|differences?\s+between|"
    r"over\s+time|multiple\s+(docs?|documents|sources|revisions)"
    r")\b",
    re.IGNORECASE,
)


def route_query(
    question: str,
    *,
    classifier: ClassifierFn | None = None,
    research_enabled: bool = False,
) -> RouteClass:
    """Rules first; optional small classifier second; uncertain → doc_qa."""
    text = question.strip()
    if not text:
        return RouteClass.DOC_QA

    if _GREETING.match(text) or _THANKS.match(text):
        return RouteClass.CONVERSATIONAL

    if research_enabled and _RESEARCH_CUE.search(text):
        return RouteClass.RESEARCH

    # Identifiers or technical cues → doc_qa before out-of-scope heuristics.
    if _HAS_IDENTIFIER.search(text) or _TECHNICAL_CUE.search(text):
        return RouteClass.DOC_QA

    if _OUT_OF_SCOPE.search(text):
        return RouteClass.OUT_OF_SCOPE

    if classifier is not None:
        predicted = classifier(text)
        if predicted is not None:
            return predicted

    # Uncertain → doc_qa (fail open toward retrieval, not chit-chat).
    return RouteClass.DOC_QA
