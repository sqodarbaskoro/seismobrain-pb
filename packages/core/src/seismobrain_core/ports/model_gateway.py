"""
File: model_gateway.py
Description: ModelGateway port for embed/rerank/verify (in-process or HTTP models service)
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

from enum import StrEnum
from typing import Protocol


class ModelGatewayKind(StrEnum):
    IN_PROCESS = "in_process"
    HTTP = "http"


class ModelGateway(Protocol):
    """Port for embedding, reranking, and verification models."""

    @property
    def kind(self) -> ModelGatewayKind:
        """Return whether this gateway is in-process or HTTP-backed."""

    def embed(self, texts: list[str], *, model_id: str) -> list[list[float]]:
        """Embed texts; concrete models service endpoints arrive in later tasks."""

    def rerank(
        self, query: str, documents: list[str], *, model_id: str
    ) -> list[int]:
        """Return document indices ordered by relevance (best first)."""

    def verify(self, claim: str, evidence: str, *, model_id: str) -> str:
        """Return a support label for claim given evidence."""
