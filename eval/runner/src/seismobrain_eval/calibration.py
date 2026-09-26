"""
File: calibration.py
Description: Passage-relevance calibration artifact writer (FR-EVAL-07)
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

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RelevanceCalibrationArtifact:
    version: str
    kind: str
    metrics: dict[str, float]
    mapping: dict[str, float]


def calibrate_relevance(
    pairs: list[tuple[float, float]],
    *,
    version: str = "rel-cal-v1",
) -> RelevanceCalibrationArtifact:
    """Fit a simple linear map from raw rerank scores to calibrated relevance."""
    if not pairs:
        raise ValueError("pairs required")
    raw_mean = sum(r for r, _ in pairs) / len(pairs)
    label_mean = sum(y for _, y in pairs) / len(pairs)
    scale = (label_mean / raw_mean) if raw_mean else 1.0
    preds = [min(1.0, max(0.0, r * scale)) for r, _ in pairs]
    mae = sum(abs(p - y) for p, (_, y) in zip(preds, pairs, strict=True)) / len(pairs)
    return RelevanceCalibrationArtifact(
        version=version,
        kind="relevance",
        metrics={"mae": mae, "n": float(len(pairs)), "scale": scale},
        mapping={"scale": scale, "bias": 0.0},
    )


def calibrate_verifier(
    pairs: list[tuple[float, str]],
    *,
    version: str = "ver-cal-v1",
) -> RelevanceCalibrationArtifact:
    """Threshold calibration on labelled sentence-evidence score/label pairs."""
    if not pairs:
        raise ValueError("pairs required")
    # Scores above threshold → supported; optimize simple cut for smoke.
    best_t = 0.5
    best_acc = -1.0
    for t in (0.3, 0.4, 0.5, 0.6, 0.7):
        correct = 0
        for score, label in pairs:
            pred = "supported" if score >= t else "unsupported"
            if (pred == "supported" and label == "supported") or (
                pred != "supported" and label != "supported"
            ):
                correct += 1
        acc = correct / len(pairs)
        if acc > best_acc:
            best_acc = acc
            best_t = t
    return RelevanceCalibrationArtifact(
        version=version,
        kind="verifier",
        metrics={"accuracy": best_acc, "n": float(len(pairs)), "threshold": best_t},
        mapping={"threshold": best_t},
    )


def write_artifact(artifact: RelevanceCalibrationArtifact, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(artifact), indent=2) + "\n", encoding="utf-8")
