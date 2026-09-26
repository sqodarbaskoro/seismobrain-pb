"""
File: sparse_ident.py
Description: ident sparse arm — exact identifier extraction and encoding (§8.4.1)
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
from typing import Protocol

from seismobrain_core.sparse_bm25_text import SparseVector

ARM_IDENT = "ident"

# Compound machine identifiers: well-alpha-12, p2/94, api.v1, host:port style parts.
_COMPOUND = re.compile(r"[A-Za-z0-9]+(?:[_\-/.:][A-Za-z0-9]+)+")
# All-caps acronyms of 2+ characters (matched on original casing).
_ACRONYM = re.compile(r"\b[A-Z]{2,}\b")
# Alphanumeric codes with at least one digit and one letter (e.g. E404, unit7).
_ALNUM_CODE = re.compile(r"\b(?=[A-Za-z0-9]*[A-Za-z])(?=[A-Za-z0-9]*\d)[A-Za-z0-9]{2,}\b")
# IPv4 addresses.
_IPV4 = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
)

_STRIP_PUNCT = re.compile(r"[_\-/.:]+")


class _Registry(Protocol):
    def get_or_assign(self, encoder_version: str, arm: str, token: str) -> int: ...


def _casefold(token: str) -> str:
    return token.casefold()


def _stripped_variant(token: str) -> str | None:
    stripped = _STRIP_PUNCT.sub("", token)
    if stripped and stripped != token:
        return stripped
    return None


def extract_identifiers(text: str) -> list[str]:
    """Return case-folded identifier tokens (punctuation preserved + stripped variants).

    No stemming. Ordinary prose tokens are ignored.
    """
    found: list[str] = []
    seen: set[str] = set()

    def _add(raw: str) -> None:
        folded = _casefold(raw)
        if folded not in seen:
            seen.add(folded)
            found.append(folded)
        variant = _stripped_variant(folded)
        if variant is not None and variant not in seen:
            seen.add(variant)
            found.append(variant)

    for match in _IPV4.finditer(text):
        _add(match.group(0))
    for match in _COMPOUND.finditer(text):
        _add(match.group(0))
    for match in _ACRONYM.finditer(text):
        _add(match.group(0))
    for match in _ALNUM_CODE.finditer(text):
        # Skip spans already covered as compound/IP.
        _add(match.group(0))

    return found


def has_identifiers(text: str) -> bool:
    """True when the text contains at least one identifier pattern."""
    return bool(extract_identifiers(text))


def encode_ident(
    text: str,
    *,
    registry: _Registry,
    encoder_version: str,
) -> SparseVector:
    """Encode identifiers with binary TF (no length normalization); IDF from Qdrant."""
    tokens = extract_identifiers(text)
    indices: list[int] = []
    values: list[float] = []
    for token in tokens:
        idx = registry.get_or_assign(encoder_version, ARM_IDENT, token)
        indices.append(idx)
        values.append(1.0)
    return SparseVector(indices=tuple(indices), values=tuple(values))
