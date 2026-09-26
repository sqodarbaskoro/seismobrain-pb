"""
File: upload_guards.py
Description: Reject dangerous uploads (macros, extreme sizes) for SEC suite
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

_MACRO_SUFFIXES = (".xlsm", ".docm", ".pptm")
_MAX_UPLOAD = 200 * 1024 * 1024


def reject_dangerous_upload(
    *, filename: str, content_type: str, size: int
) -> bool:
    """Return True when the upload must be rejected."""
    lower = filename.lower()
    if any(lower.endswith(suf) for suf in _MACRO_SUFFIXES):
        return True
    if "macro" in content_type.lower():
        return True
    if size > _MAX_UPLOAD:
        return True
    return False
