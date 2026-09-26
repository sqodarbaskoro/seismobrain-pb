"""
File: authorization_guard.py
Description: AuthorizationGuard port (framework-free) for metadata re-checks
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


class AuthorizationGuard(Protocol):
    """Re-check candidates against the metadata store (full cache semantics in T0b.8)."""

    def check_read(self, user_id: str, document_id: str) -> bool:
        """Return True if the user currently has read permission on the document."""
