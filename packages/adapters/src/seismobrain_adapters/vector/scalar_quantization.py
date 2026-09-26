"""
File: scalar_quantization.py
Description: Dense-vector scalar quantization with rescoring (FR-IDX-05)
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

from qdrant_client.http import models as qm

from seismobrain_adapters.vector.qdrant_base import QdrantVectorStoreBase


@dataclass(frozen=True, slots=True)
class ScalarQuantizationPolicy:
    """Enable int8 scalar quantization above a configurable collection size."""

    min_points: int = 10_000
    always_ram: bool = True
    rescore: bool = True
    oversampling: float = 2.0

    def should_enable(self, point_count: int) -> bool:
        return point_count >= self.min_points

    def qdrant_config(self) -> qm.ScalarQuantization:
        return qm.ScalarQuantization(
            scalar=qm.ScalarQuantizationConfig(
                type=qm.ScalarType.INT8,
                quantile=0.99,
                always_ram=self.always_ram,
            )
        )

    def search_params(self) -> qm.SearchParams:
        return qm.SearchParams(
            quantization=qm.QuantizationSearchParams(
                rescore=self.rescore,
                oversampling=self.oversampling,
            )
        )


def apply_scalar_quantization_if_needed(
    store: QdrantVectorStoreBase,
    collection: str,
    *,
    policy: ScalarQuantizationPolicy | None = None,
) -> bool:
    """Update collection quantization when size exceeds threshold. Returns enabled."""
    pol = policy or ScalarQuantizationPolicy()
    count = store.count(collection)
    if not pol.should_enable(count):
        return False
    store.client.update_collection(
        collection_name=collection,
        quantization_config=pol.qdrant_config(),
    )
    return True


def recall_at_k(
    ranked_ids: list[str], relevant_ids: list[str], *, k: int = 10
) -> float:
    if not relevant_ids:
        return 0.0
    top = set(ranked_ids[:k])
    hits = sum(1 for r in relevant_ids if r in top)
    return hits / len(relevant_ids)


def measure_quantization_recall_loss(
    full_ranked: list[str],
    quantized_ranked: list[str],
    relevant_ids: list[str],
    *,
    k: int = 10,
) -> float:
    """Absolute recall@k drop in percentage points (0–100 scale points as fractions)."""
    full = recall_at_k(full_ranked, relevant_ids, k=k)
    quant = recall_at_k(quantized_ranked, relevant_ids, k=k)
    return max(0.0, full - quant)
