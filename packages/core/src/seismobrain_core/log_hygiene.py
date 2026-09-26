"""
File: log_hygiene.py
Description: Redaction helpers and log filter for SEC-20 hygiene
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
from typing import Any

_SENSITIVE_KEYS = frozenset(
    {
        "password",
        "secret",
        "token",
        "api_key",
        "jwt_secret",
        "master_key",
        "prompt",
        "document_text",
        "evidence_text",
        "chunk_text",
    }
)
_SENSITIVE_TOKENS = (
    "password",
    "secret",
    "token",
    "api_key",
    "jwt",
    "prompt",
    "document_text",
    "evidence_text",
)


def redact_mapping(payload: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in payload.items():
        lowered = key.lower()
        if lowered in _SENSITIVE_KEYS or any(
            token in lowered for token in ("secret", "password", "token")
        ):
            cleaned[key] = "[REDACTED]"
        elif isinstance(value, dict):
            cleaned[key] = redact_mapping(value)
        else:
            cleaned[key] = value
    return cleaned


class SafeLogFilter(logging.Filter):
    """Drop log records that appear to contain secrets/prompts unless opted in."""

    def __init__(self, *, llm_trace_enabled: bool = False) -> None:
        super().__init__()
        self.llm_trace_enabled = llm_trace_enabled

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage().lower()
        for token in _SENSITIVE_TOKENS:
            if token == "prompt" and self.llm_trace_enabled:
                continue
            if token in message:
                return False
        return True
