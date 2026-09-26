"""
File: verifier_set.py
Description: Synthetic class-balanced verifier evaluation set builder (FR-EVAL-09)
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

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VerifierPair:
    sentence: str
    evidence: str
    label: str
    tag: str = ""


def build_verifier_set(*, size: int = 300) -> list[VerifierPair]:
    """Build ≥size class-balanced triples including near-miss numeric errors."""
    labels = ["supported", "partial", "unsupported", "no_citation"]
    pairs: list[VerifierPair] = []
    i = 0
    while len(pairs) < size:
        label = labels[i % len(labels)]
        if label == "supported":
            pairs.append(
                VerifierPair(
                    sentence=f"Limit is 6 knots case {i}.",
                    evidence="Normal limit is 6 knots.",
                    label=label,
                )
            )
        elif label == "partial":
            pairs.append(
                VerifierPair(
                    sentence=f"Limit is about 6 knots case {i}.",
                    evidence="Normal limit is 6 knots under calm seas.",
                    label=label,
                )
            )
        elif label == "unsupported":
            # Near-miss: right number, wrong condition / unit.
            pairs.append(
                VerifierPair(
                    sentence=f"Normal limit is 9 knots case {i}.",
                    evidence="Normal limit is 6 knots. Emergency limit is 9 knots.",
                    label=label,
                    tag="near_miss_numeric",
                )
            )
        else:
            pairs.append(
                VerifierPair(
                    sentence=f"Undocumented claim {i}.",
                    evidence="Torque is 40 Nm.",
                    label=label,
                )
            )
        i += 1
    return pairs
