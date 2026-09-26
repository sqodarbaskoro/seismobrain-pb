"""
File: sparse_term_registry.py
Description: SparseTermRegistry port for collision-free sparse token indices
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


class SparseTermRegistry(Protocol):
    """Assigns stable collision-free indices per (encoder_version, arm, token)."""

    def get_or_assign(self, encoder_version: str, arm: str, token: str) -> int:
        """Return existing index or allocate a new one."""

    def close(self) -> None:
        """Release resources."""
