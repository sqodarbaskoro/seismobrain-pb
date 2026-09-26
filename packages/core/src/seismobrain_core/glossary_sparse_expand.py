"""
File: glossary_sparse_expand.py
Description: Workspace glossary expands sparse query only (FR-QRY-07)
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
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExpandedQuery:
    original: str
    dense_text: str
    sparse_text: str
    expansions: tuple[str, ...]


def expand_sparse_with_glossary(
    query: str,
    glossary: Mapping[str, str],
) -> ExpandedQuery:
    """
    Expand acronyms/synonyms into the sparse arm only.
    Dense query text stays unchanged.
    """
    expansions: list[str] = []
    sparse = query
    # Longer keys first so multi-word phrases win.
    for key in sorted(glossary.keys(), key=len, reverse=True):
        pattern = re.compile(rf"\b{re.escape(key)}\b", re.IGNORECASE)
        if pattern.search(sparse):
            value = glossary[key]
            expansions.append(value)
            sparse = pattern.sub(f"{key} {value}", sparse, count=1)
    return ExpandedQuery(
        original=query,
        dense_text=query,
        sparse_text=sparse,
        expansions=tuple(expansions),
    )
