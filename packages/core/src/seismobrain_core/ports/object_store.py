"""
File: object_store.py
Description: ObjectStore port (framework-free) for blob storage
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


class ObjectStore(Protocol):
    """Port for opaque object/blob storage."""

    def put(self, key: str, data: bytes) -> None:
        """Store bytes at key."""

    def get(self, key: str) -> bytes:
        """Fetch bytes for key; raise KeyError if missing."""

    def delete(self, key: str) -> None:
        """Delete key if present."""

    def exists(self, key: str) -> bool:
        """Return True if key exists."""

    def list_keys(self, prefix: str = "") -> list[str]:
        """List keys with the given prefix."""
