"""
File: identifiers.py
Description: Configurable identifier detection for queries (FR-QRY-03)
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
from dataclasses import dataclass, field

# Default patterns: compound ids, error codes, IPv4, all-caps acronyms (2+).
_DEFAULT_PATTERNS: tuple[str, ...] = (
    r"[A-Za-z0-9]+(?:[_\-/.:][A-Za-z0-9]+)+",
    r"\b[A-Za-z]-?\d{2,}\b",
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b",
    r"\b[A-Z]{2,}\b",
)


@dataclass(frozen=True, slots=True)
class IdentifierDetector:
    """Detects machine identifiers; patterns are configurable per workspace."""

    extra_patterns: tuple[str, ...] = ()
    _compiled: tuple[re.Pattern[str], ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        patterns = _DEFAULT_PATTERNS + self.extra_patterns
        object.__setattr__(
            self,
            "_compiled",
            tuple(re.compile(p) for p in patterns),
        )

    def detect(self, text: str) -> list[str]:
        found: list[str] = []
        seen: set[str] = set()
        for pattern in self._compiled:
            for match in pattern.finditer(text):
                token = match.group(0)
                if token not in seen:
                    seen.add(token)
                    found.append(token)
        return found


_DEFAULT = IdentifierDetector()


def detect_identifiers(text: str) -> list[str]:
    """Detect identifiers with default patterns; return verbatim spans."""
    return _DEFAULT.detect(text)


def preserve_identifiers(
    original: str,
    rewritten: str,
    identifiers: list[str] | None = None,
) -> str:
    """Discard rewrite if any identifier from original is missing (verbatim)."""
    ids = identifiers if identifiers is not None else detect_identifiers(original)
    for token in ids:
        if token not in rewritten:
            return original
    return rewritten
