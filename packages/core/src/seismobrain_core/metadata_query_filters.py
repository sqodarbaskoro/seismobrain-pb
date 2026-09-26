"""
File: metadata_query_filters.py
Description: Explicit hard filters vs inferred soft boosts (FR-QRY-08)
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
from typing import Any

_EXPLICIT = re.compile(
    r"""(?ix)
    \b(?:doc[_ ]?type|type)\s*[:=]\s*(?P<doc_type>\w+)
    | \b(?:language|lang)\s*[:=]\s*(?P<language>\w+)
    | \b(?:author)\s*[:=]\s*(?P<author>[\w.\-]+)
    | \b(?:tag)\s*[:=]\s*(?P<tag>[\w.\-]+)
    """
)

_INFERRED_DOC_TYPE = re.compile(
    r"\b(pdf|manual|procedure|drawing|spec(?:ification)?)\b", re.IGNORECASE
)
_INFERRED_LANG = re.compile(r"\b(english|indonesian|malay|french)\b", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class MetadataQueryPlan:
    hard_filters: dict[str, Any]
    soft_boosts: dict[str, Any]
    residual_question: str


def plan_metadata_filters(question: str) -> MetadataQueryPlan:
    """Explicit key=value becomes hard filter; inferred cues become soft boosts."""
    hard: dict[str, Any] = {}
    residual = question
    for match in _EXPLICIT.finditer(question):
        for key, value in match.groupdict().items():
            if value:
                hard[key] = value.lower() if key != "author" else value
        residual = residual[: match.start()] + residual[match.end() :]
    residual = re.sub(r"\s{2,}", " ", residual).strip(" ,")

    soft: dict[str, Any] = {}
    doc = _INFERRED_DOC_TYPE.search(residual)
    if doc and "doc_type" not in hard:
        soft["doc_type"] = doc.group(1).lower()
    lang = _INFERRED_LANG.search(residual)
    if lang and "language" not in hard:
        soft["language"] = lang.group(1).lower()

    return MetadataQueryPlan(
        hard_filters=hard,
        soft_boosts=soft,
        residual_question=residual,
    )
