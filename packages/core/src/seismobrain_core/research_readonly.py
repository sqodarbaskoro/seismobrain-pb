"""
File: research_readonly.py
Description: Research mode is read-only — no side-effecting tools (FR-AGT-07)
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

from collections.abc import Sequence

SIDE_EFFECT_TOOLS = frozenset(
    {
        "write_file",
        "delete_document",
        "send_email",
        "http_post",
        "run_shell",
        "update_acl",
    }
)


class SideEffectToolError(PermissionError):
    """Raised when research mode attempts a side-effecting tool."""


def assert_research_readonly(requested_tools: Sequence[str]) -> None:
    bad = [t for t in requested_tools if t in SIDE_EFFECT_TOOLS]
    if bad:
        raise SideEffectToolError(f"research mode forbids tools: {bad}")


def research_allowed_tools() -> tuple[str, ...]:
    """Only read-only retrieval helpers are permitted."""
    return ("retrieve", "rerank", "read_evidence")
