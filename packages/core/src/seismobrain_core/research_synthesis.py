"""
File: research_synthesis.py
Description: Single synthesis over pooled evidence with verification (FR-AGT-04)
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

from seismobrain_core.grounding_balanced import GroundingMode, apply_grounding
from seismobrain_core.grounding_strict import apply_strict_grounding
from seismobrain_core.research_pool import PooledEvidence
from seismobrain_core.sentence_verifier import VerifiedSentence

_SENTENCE = re.compile(r"(?<=[.!?])\s+")
_ETAG = re.compile(r"\[(E\d+)\]")


@dataclass(frozen=True, slots=True)
class ResearchSynthesisResult:
    answer: str
    grounding_mode: GroundingMode
    supported_ratio: float
    faithfulness_ok: bool


def _lexical_verify(
    draft: str, evidence: Sequence[PooledEvidence]
) -> list[VerifiedSentence]:
    by_id = {e.evidence_id: e.text.lower() for e in evidence}
    out: list[VerifiedSentence] = []
    for raw in [s.strip() for s in _SENTENCE.split(draft.strip()) if s.strip()]:
        tags = tuple(_ETAG.findall(raw))
        if not tags:
            out.append(VerifiedSentence(raw, (), "no_citation"))
            continue
        claim = _ETAG.sub("", raw).strip().lower()
        joined = " ".join(by_id[t] for t in tags if t in by_id)
        claim_tokens = set(re.findall(r"[a-z0-9]+", claim))
        ev_tokens = set(re.findall(r"[a-z0-9]+", joined))
        if claim_tokens and len(claim_tokens & ev_tokens) / len(claim_tokens) >= 0.6:
            label = "supported"
        else:
            label = "unsupported"
        out.append(VerifiedSentence(raw, tags, label))
    return out


def synthesize_research_answer(
    *,
    question: str,
    evidence: Sequence[PooledEvidence],
    draft: str,
    mode: GroundingMode = GroundingMode.STRICT,
    standard_supported_ratio: float = 0.8,
) -> ResearchSynthesisResult:
    """Single synthesis path: verify draft against pooled evidence."""
    _ = question
    verified = _lexical_verify(draft, evidence)
    if mode is GroundingMode.STRICT:
        grounding, _refusal = apply_strict_grounding(verified)
        sentences = grounding.sentences
    else:
        grounding = apply_grounding(verified, mode=GroundingMode.BALANCED)
        sentences = grounding.sentences
    factual = [v for v in verified if v.label != "no_citation"]
    total = len(factual) or 1
    supported = sum(1 for s in factual if s.label == "supported")
    ratio = supported / total
    answer = " ".join(s.text for s in sentences) if sentences else draft
    return ResearchSynthesisResult(
        answer=answer,
        grounding_mode=mode,
        supported_ratio=ratio,
        faithfulness_ok=ratio >= standard_supported_ratio,
    )


def faithfulness_vs_standard(
    research: ResearchSynthesisResult, standard: Sequence[VerifiedSentence]
) -> bool:
    factual = [s for s in standard if s.label != "no_citation"]
    std_total = len(factual) or 1
    std_ratio = sum(1 for s in factual if s.label == "supported") / std_total
    return research.supported_ratio >= std_ratio
