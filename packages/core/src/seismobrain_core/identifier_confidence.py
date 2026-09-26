"""
File: identifier_confidence.py
Description: Identifier confidence classes and ident arm weights (FR-RET-14)
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
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from seismobrain_core.identifiers import detect_identifiers

# Dates, version strings, file paths, section numbers — excluded by default.
_EXCLUDED = re.compile(
    r"""(?x)
    ^\d{4}-\d{2}-\d{2}$
    | ^v?\d+(?:\.\d+)+$
    | ^(?:[A-Za-z]:)?(?:/|\\)?[\w.\-]+(?:/|\\)[\w./\\-]+$
    | ^(?:sec(?:tion)?|§)\s*\d+(?:\.\d+)*$
    | ^section$
    """,
    re.IGNORECASE,
)

_STRUCTURED = re.compile(
    r"^[A-Za-z0-9]+(?:[_\-/.:][A-Za-z0-9]+)+$|^[A-Za-z]-?\d{2,}$"
)
_ACRONYM = re.compile(r"^[A-Z]{2,}$")


class IdentifierConfidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


WEIGHTS = {
    IdentifierConfidence.HIGH: 1.5,
    IdentifierConfidence.MEDIUM: 1.2,
    IdentifierConfidence.LOW: 1.0,
}


@dataclass(frozen=True, slots=True)
class ClassifiedIdentifier:
    token: str
    confidence: IdentifierConfidence


@dataclass(frozen=True, slots=True)
class IdentifierConfidenceResult:
    identifiers: tuple[ClassifiedIdentifier, ...]
    highest: IdentifierConfidence | None
    ident_weight: float
    skip_ident_arm: bool


def classify_identifier(
    token: str,
    *,
    high_patterns: Sequence[str] = (),
    glossary: Sequence[str] = (),
) -> IdentifierConfidence | None:
    if _EXCLUDED.match(token):
        return None
    high_set = {g.casefold() for g in glossary}
    if token.casefold() in high_set:
        return IdentifierConfidence.HIGH
    for pattern in high_patterns:
        if re.fullmatch(pattern, token):
            return IdentifierConfidence.HIGH
    if _STRUCTURED.match(token):
        return IdentifierConfidence.MEDIUM
    if _ACRONYM.match(token):
        return IdentifierConfidence.LOW
    return IdentifierConfidence.LOW


def analyze_identifiers(
    text: str,
    *,
    high_patterns: Sequence[str] = (),
    glossary: Sequence[str] = (),
) -> IdentifierConfidenceResult:
    classified: list[ClassifiedIdentifier] = []
    for token in detect_identifiers(text):
        level = classify_identifier(
            token, high_patterns=high_patterns, glossary=glossary
        )
        if level is None:
            continue
        classified.append(ClassifiedIdentifier(token=token, confidence=level))
    if not classified:
        return IdentifierConfidenceResult(
            identifiers=(),
            highest=None,
            ident_weight=0.0,
            skip_ident_arm=True,
        )
    order = {
        IdentifierConfidence.LOW: 0,
        IdentifierConfidence.MEDIUM: 1,
        IdentifierConfidence.HIGH: 2,
    }
    highest = max(classified, key=lambda c: order[c.confidence]).confidence
    skip = highest is IdentifierConfidence.LOW and all(
        c.confidence is IdentifierConfidence.LOW for c in classified
    )
    # low-only MAY skip; we skip by default for low-only.
    return IdentifierConfidenceResult(
        identifiers=tuple(classified),
        highest=highest,
        ident_weight=WEIGHTS[highest],
        skip_ident_arm=skip,
    )


def over_detection_rate(
    predicted: Sequence[str], gold: Sequence[str]
) -> float:
    """Fraction of predicted identifiers not in the gold set."""
    if not predicted:
        return 0.0
    gold_set = set(gold)
    false = sum(1 for p in predicted if p not in gold_set)
    return false / len(predicted)
