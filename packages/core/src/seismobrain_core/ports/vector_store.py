"""
File: vector_store.py
Description: VectorStore port (framework-free) for dense vector index operations
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

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class VectorPoint:
    id: str
    vector: list[float]
    payload: dict[str, Any] = field(default_factory=dict)


class VectorStore(Protocol):
    """Port for vector index operations. Implementations live in packages/adapters."""

    def ensure_collection(self, name: str, vector_size: int) -> None:
        """Create the named collection if missing."""

    def upsert(self, collection: str, points: list[VectorPoint]) -> None:
        """Insert or replace points."""

    def search(
        self, collection: str, query_vector: list[float], limit: int = 10
    ) -> list[VectorPoint]:
        """Nearest-neighbor search; returned points include payload (vector may be empty)."""

    def count(self, collection: str) -> int:
        """Return the number of points in the collection."""

    def close(self) -> None:
        """Release resources (no-op when not required)."""
