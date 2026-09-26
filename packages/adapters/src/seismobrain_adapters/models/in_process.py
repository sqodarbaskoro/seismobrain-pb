"""
File: in_process.py
Description: In-process CPU ModelGateway for Starter tier (T0c.8 / T0c.9)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-16
Version: 0.2.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

from seismobrain_core.ports import ModelGatewayKind
from seismobrain_models.runtime import dense_embed, rerank, verify_claim


class InProcessModelGateway:
    """Starter ModelGateway running deterministic CPU models in-process."""

    def __init__(self, *, embed_dim: int = 32) -> None:
        self._embed_dim = embed_dim

    @property
    def kind(self) -> ModelGatewayKind:
        return ModelGatewayKind.IN_PROCESS

    def embed(self, texts: list[str], *, model_id: str) -> list[list[float]]:
        _ = model_id
        return dense_embed(texts, dim=self._embed_dim)

    def rerank(
        self, query: str, documents: list[str], *, model_id: str
    ) -> list[int]:
        _ = model_id
        return rerank(query, documents)

    def verify(self, claim: str, evidence: str, *, model_id: str) -> str:
        _ = model_id
        return verify_claim(claim, evidence)
