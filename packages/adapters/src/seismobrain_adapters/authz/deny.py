"""
File: deny.py
Description: Default-deny AuthorizationGuard stub used until T0b.8 implements caching
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


class DenyAllAuthorizationGuard:
    """Fail-closed stub guard for DI wiring before the real guard lands."""

    def check_read(self, user_id: str, document_id: str) -> bool:
        _ = user_id, document_id
        return False
