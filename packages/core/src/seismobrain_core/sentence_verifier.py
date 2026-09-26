"""
File: sentence_verifier.py
Description: Sentence support labels via ModelGateway (FR-GEN-04)
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

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from seismobrain_core.ports.model_gateway import ModelGateway
from seismobrain_core.sentence_tag_validation import ValidatedSentence

SUPPORT_LABELS = frozenset({"supported", "partial", "unsupported", "no_citation"})


@dataclass(frozen=True, slots=True)
class VerifiedSentence:
    text: str
    evidence_ids: tuple[str, ...]
    label: str


@dataclass(frozen=True, slots=True)
class VerifierMetrics:
    counts: dict[str, int]
    unsupported_to_supported: float
    supported_precision: float


def verify_sentences(
    sentences: Sequence[ValidatedSentence],
    *,
    evidence_text: Mapping[str, str],
    gateway: ModelGateway,
    model_id: str = "cpu-verify",
) -> list[VerifiedSentence]:
    out: list[VerifiedSentence] = []
    for sentence in sentences:
        if not sentence.evidence_ids:
            out.append(
                VerifiedSentence(
                    text=sentence.text, evidence_ids=(), label="no_citation"
                )
            )
            continue
        joined = "\n".join(
            evidence_text[eid] for eid in sentence.evidence_ids if eid in evidence_text
        )
        claim = sentence.text
        for eid in sentence.evidence_ids:
            claim = claim.replace(f"[{eid}]", "")
        label = gateway.verify(claim.strip(), joined, model_id=model_id)
        if label not in SUPPORT_LABELS:
            label = "unsupported"
        out.append(
            VerifiedSentence(
                text=sentence.text, evidence_ids=sentence.evidence_ids, label=label
            )
        )
    return out


def class_metrics(
    predicted: Sequence[str], labelled: Sequence[str]
) -> VerifierMetrics:
    counts = dict(Counter(predicted))
    pairs = list(zip(predicted, labelled, strict=True))
    unsupported = [p for p, y in pairs if y == "unsupported"]
    false_accept = sum(1 for p in unsupported if p == "supported")
    rate = (false_accept / len(unsupported)) if unsupported else 0.0
    supported_pred = [y for p, y in pairs if p == "supported"]
    precision = (
        sum(1 for y in supported_pred if y == "supported") / len(supported_pred)
        if supported_pred
        else 1.0
    )
    return VerifierMetrics(
        counts=counts,
        unsupported_to_supported=rate,
        supported_precision=precision,
    )
