"""
File: support_label_stages.py
Description: Pre-verification vs delivered support labels (FR-GEN-13)
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

from seismobrain_core.grounding_balanced import ReleasedSentence
from seismobrain_core.sentence_verifier import VerifiedSentence


@dataclass(frozen=True, slots=True)
class SupportLabelRecord:
    pre_verification: tuple[str, ...]
    delivered: tuple[str, ...]
    pre_supported_rate: float
    delivered_supported_rate: float


def _rate(labels: Sequence[str], target: str = "supported") -> float:
    if not labels:
        return 0.0
    return sum(1 for label in labels if label == target) / len(labels)


def record_support_stages(
    pre: Sequence[VerifiedSentence],
    delivered: Sequence[ReleasedSentence],
) -> SupportLabelRecord:
    pre_labels = tuple(s.label for s in pre)
    delivered_labels = tuple(s.label for s in delivered)
    return SupportLabelRecord(
        pre_verification=pre_labels,
        delivered=delivered_labels,
        pre_supported_rate=_rate(pre_labels),
        delivered_supported_rate=_rate(delivered_labels),
    )
