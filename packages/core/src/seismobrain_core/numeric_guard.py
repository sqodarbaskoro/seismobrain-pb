"""
File: numeric_guard.py
Description: Numeric consistency guard after unit normalization (FR-GEN-07)
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
from dataclasses import dataclass

_NUM_UNIT = re.compile(
    r"(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>knots?|nm|kn|kts?|m|mm|cm|in|ft)?",
    re.IGNORECASE,
)

_UNIT_ALIASES = {
    "knot": "kn",
    "knots": "kn",
    "kts": "kn",
    "kt": "kn",
    "kn": "kn",
    "nm": "nm",
}


@dataclass(frozen=True, slots=True)
class NumericGuardResult:
    ok: bool
    mismatches: tuple[str, ...]


def _normalize_unit(unit: str | None) -> str:
    if not unit:
        return ""
    return _UNIT_ALIASES.get(unit.lower(), unit.lower())


def extract_quantities(text: str) -> set[tuple[float, str]]:
    out: set[tuple[float, str]] = set()
    for match in _NUM_UNIT.finditer(text):
        value = float(match.group("value"))
        unit = _normalize_unit(match.group("unit"))
        out.add((value, unit))
    return out


def check_numeric_consistency(sentence: str, evidence: str) -> NumericGuardResult:
    """Numbers/units in sentence must appear in evidence after normalization."""
    sent_q = extract_quantities(sentence)
    if not sent_q:
        return NumericGuardResult(ok=True, mismatches=())
    evid_q = extract_quantities(evidence)
    mismatches = [
        f"{value} {unit}".strip()
        for value, unit in sorted(sent_q)
        if (value, unit) not in evid_q
    ]
    return NumericGuardResult(ok=not mismatches, mismatches=tuple(mismatches))
