"""
File: transport.py
Description: Injectable HTTP JSON transport for LLM adapters (no sockets in tests)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-18
Version: 0.1.1
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, cast

import httpx


class JsonHttpTransport(Protocol):
    def post_json(
        self, url: str, *, headers: dict[str, str], body: dict[str, Any]
    ) -> dict[str, Any]:
        """POST JSON and return parsed response body."""


@dataclass
class RecordingTransport:
    """Test double that records requests and returns a canned response."""

    response: dict[str, Any]
    calls: list[dict[str, Any]] = field(default_factory=list)
    error: Exception | None = None

    def post_json(
        self, url: str, *, headers: dict[str, str], body: dict[str, Any]
    ) -> dict[str, Any]:
        self.calls.append({"url": url, "headers": headers, "body": body})
        if self.error is not None:
            raise self.error
        return self.response


@dataclass
class HttpxJsonTransport:
    """Real HTTP JSON transport for production LLM egress."""

    timeout_seconds: float = 30.0

    def post_json(
        self, url: str, *, headers: dict[str, str], body: dict[str, Any]
    ) -> dict[str, Any]:
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(url, headers=headers, json=body)
            response.raise_for_status()
            return cast(dict[str, Any], response.json())
