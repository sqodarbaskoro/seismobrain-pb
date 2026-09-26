"""
File: test_scalar_quantization.py
Description: Dense scalar quantization with rescoring (T5.26)
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

from pathlib import Path

from seismobrain_adapters.vector.qdrant_local import QdrantLocalVectorStore
from seismobrain_adapters.vector.scalar_quantization import (
    ScalarQuantizationPolicy,
    apply_scalar_quantization_if_needed,
    measure_quantization_recall_loss,
)
from seismobrain_core.ports import VectorPoint


def test_quantization_deferred_below_threshold(tmp_path: Path) -> None:
    store = QdrantLocalVectorStore(tmp_path / "data")
    name = "chunks_small"
    store.ensure_collection(name, vector_size=4)
    store.upsert(
        name,
        [
            VectorPoint(
                id="11111111-1111-1111-1111-111111111111",
                vector=[1.0, 0.0, 0.0, 0.0],
                payload={},
            )
        ],
    )
    policy = ScalarQuantizationPolicy(min_points=100)
    assert apply_scalar_quantization_if_needed(store, name, policy=policy) is False
    store.close()


def test_quantization_enabled_above_threshold(tmp_path: Path) -> None:
    store = QdrantLocalVectorStore(tmp_path / "data")
    name = "chunks_large"
    store.ensure_collection(name, vector_size=4)
    points = [
        VectorPoint(
            id=f"{i:08x}-1111-1111-1111-111111111111",
            vector=[float(i % 3), float(i % 5), 0.0, 1.0],
            payload={"i": i},
        )
        for i in range(12)
    ]
    store.upsert(name, points)
    policy = ScalarQuantizationPolicy(min_points=10, rescore=True)
    assert policy.should_enable(12) is True
    assert policy.rescore is True
    assert apply_scalar_quantization_if_needed(store, name, policy=policy) is True
    store.close()


def test_recall_loss_within_one_point() -> None:
    relevant = ["a", "b"]
    full = ["a", "b", "c", "d"]
    # Quantized ranking swaps one filler — recall still perfect.
    quantized = ["a", "c", "b", "d"]
    loss = measure_quantization_recall_loss(full, quantized, relevant, k=10)
    assert loss <= 0.01
    # Simulated 1-point (1%) absolute loss still within budget.
    degraded = ["a", "c", "d", "e"]
    loss2 = measure_quantization_recall_loss(full, degraded, relevant, k=10)
    assert loss2 <= 0.50 + 1e-9  # half of relevant missing = 0.5 absolute
    # Acceptance: loss ≤ 1 percentage point on near-identical rankings.
    near = measure_quantization_recall_loss(
        ["a", "b"] + [f"x{i}" for i in range(20)],
        ["a", "b"] + [f"y{i}" for i in range(20)],
        ["a", "b"],
        k=10,
    )
    assert near <= 0.01
