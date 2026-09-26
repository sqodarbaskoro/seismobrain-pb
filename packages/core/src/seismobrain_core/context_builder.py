"""
File: context_builder.py
Description: Evidence IDs E1..En, ordering, token budget (FR-RET-08)
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

from collections.abc import Callable, Sequence
from dataclasses import dataclass

TokenCounter = Callable[[str], int]


@dataclass(frozen=True, slots=True)
class EvidenceItem:
    chunk_id: str
    text: str
    relevance: float


@dataclass(frozen=True, slots=True)
class BuiltContext:
    blocks: tuple[tuple[str, EvidenceItem], ...]  # (E1, item)...
    dropped: tuple[EvidenceItem, ...]
    token_count: int


def whitespace_tokens(text: str) -> int:
    return len(text.split()) if text.strip() else 0


def build_context(
    evidence: Sequence[EvidenceItem],
    *,
    max_tokens: int,
    token_counter: TokenCounter = whitespace_tokens,
) -> BuiltContext:
    """Assign E1..En by relevance, enforce budget, record drops."""
    ordered = sorted(evidence, key=lambda e: (-e.relevance, e.chunk_id))
    blocks: list[tuple[str, EvidenceItem]] = []
    dropped: list[EvidenceItem] = []
    used = 0
    for item in ordered:
        cost = token_counter(item.text)
        if used + cost > max_tokens and blocks:
            dropped.append(item)
            continue
        if used + cost > max_tokens and not blocks:
            # Always include at least one if possible by truncating budget check.
            if cost > max_tokens:
                dropped.append(item)
                continue
        label = f"E{len(blocks) + 1}"
        blocks.append((label, item))
        used += cost
    return BuiltContext(blocks=tuple(blocks), dropped=tuple(dropped), token_count=used)
