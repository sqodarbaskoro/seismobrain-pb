"""
File: evidence_snapshot_store.py
Description: EvidenceSnapshotStore port for immutable evidence text blobs
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


class EvidenceSnapshotStore(Protocol):
    """Immutable store for evidence (and prompt) snapshot text."""

    def put(self, text: str) -> str:
        """Persist snapshot text and return a blob URI."""

    def get(self, uri: str) -> str:
        """Fetch snapshot text by URI; raise KeyError if missing."""
