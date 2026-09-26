"""
File: answerability_trained.py
Description: Trained global-base answerability gate (FR-RET-05, SEC-27)
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

from collections.abc import Sequence
from dataclasses import dataclass

from seismobrain_core.answerability import EvidenceSnippet, GateDecision


@dataclass(frozen=True, slots=True)
class GateModelCard:
    model_id: str
    training_corpus: str  # must be public_or_synthetic for global base
    tenant_private_data: bool = False


@dataclass(frozen=True, slots=True)
class TrainedGateScores:
    score: float
    threshold: float


def assert_global_base_training(card: GateModelCard) -> None:
    if card.tenant_private_data:
        raise ValueError("global base must not train on tenant private data (SEC-27)")
    if card.training_corpus not in {"public", "synthetic", "public_or_synthetic"}:
        raise ValueError("global base requires public/synthetic training corpus")


def score_answerability(
    query: str,
    evidence: Sequence[EvidenceSnippet],
    *,
    threshold: float = 0.5,
) -> TrainedGateScores:
    """Lightweight logistic-style score over overlap and relevance features."""
    if not evidence:
        return TrainedGateScores(score=0.0, threshold=threshold)
    q = set(query.lower().split())
    overlaps: list[float] = []
    rels: list[float] = []
    for item in evidence:
        e = set(item.text.lower().split())
        overlaps.append(len(q & e) / max(len(q), 1))
        rels.append(item.relevance)
    feature = 0.6 * max(overlaps) + 0.4 * max(rels)
    # Squash to (0,1)
    score = 1.0 / (1.0 + pow(2.718281828, -4 * (feature - 0.35)))
    return TrainedGateScores(score=score, threshold=threshold)


def trained_answerability(
    query: str,
    evidence: Sequence[EvidenceSnippet],
    *,
    card: GateModelCard,
    threshold: float = 0.5,
) -> GateDecision:
    assert_global_base_training(card)
    scored = score_answerability(query, evidence, threshold=threshold)
    if scored.score >= scored.threshold:
        return GateDecision(answerable=True, reason=f"trained:{card.model_id}")
    return GateDecision(answerable=False, reason="insufficient_evidence")
