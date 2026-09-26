"""
File: starter_bind.py
Description: Warn when Starter tier binds outside loopback (SEC-22)
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

import logging

from seismobrain_api.config import Settings

_LOG = logging.getLogger("seismobrain.api.starter_bind")
_LOOPBACK = frozenset({"127.0.0.1", "::1", "localhost"})


def warn_if_starter_exposed(settings: Settings) -> str | None:
    """Return and log a warning when Starter binds outside loopback."""
    if settings.sb_tier != "starter":
        return None
    if settings.bind_host in _LOOPBACK:
        return None
    message = (
        f"SECURITY WARNING: Starter tier is exposed on bind host "
        f"{settings.bind_host!r}; prefer 127.0.0.1"
    )
    _LOG.warning(message)
    return message
