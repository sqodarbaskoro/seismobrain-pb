"""
File: sparse_term_registry.py
Description: In-memory collision-free sparse term index allocator (PRD §8.4.3)
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

import threading


class InMemorySparseTermRegistry:
    """Append-only sequential allocator: (encoder_version, arm, token) → idx.

    Distinct tokens never share an index within the same encoder version and arm.
    Indices are not derived from hashing, so collisions cannot occur.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # (encoder_version, arm, token) -> idx
        self._token_to_idx: dict[tuple[str, str, str], int] = {}
        # (encoder_version, arm) -> next idx
        self._next_idx: dict[tuple[str, str], int] = {}

    def get_or_assign(self, encoder_version: str, arm: str, token: str) -> int:
        """Return existing index or allocate the next sequential index."""
        key = (encoder_version, arm, token)
        with self._lock:
            existing = self._token_to_idx.get(key)
            if existing is not None:
                return existing
            scope = (encoder_version, arm)
            idx = self._next_idx.get(scope, 0)
            self._token_to_idx[key] = idx
            self._next_idx[scope] = idx + 1
            return idx

    def lookup(self, encoder_version: str, arm: str, token: str) -> int | None:
        """Return index if registered; None for missing query tokens (dropped)."""
        with self._lock:
            return self._token_to_idx.get((encoder_version, arm, token))

    def close(self) -> None:
        """Release resources (no-op for in-memory)."""
        return None
