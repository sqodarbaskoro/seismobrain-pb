"""
File: embedding_cache.py
Description: EmbeddingCache port (framework-free) for reusable embedding vectors
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

from typing import Protocol


class EmbeddingCache(Protocol):
    """Cache keyed by (text_hash, model_id, model_revision)."""

    def get(
        self, text_hash: str, model_id: str, model_revision: str
    ) -> list[float] | None:
        """Return cached vector or None."""

    def put(
        self,
        text_hash: str,
        model_id: str,
        model_revision: str,
        *,
        vector: list[float],
    ) -> None:
        """Store vector; may evict entries to stay within size bound."""

    def size_bytes(self) -> int:
        """Approximate total cached vector payload size in bytes."""
