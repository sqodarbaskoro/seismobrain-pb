"""
File: test_research_readonly.py
Description: Research mode read-only no side-effecting tools (T5.7)
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

import pytest

from seismobrain_core.research_readonly import (
    SideEffectToolError,
    assert_research_readonly,
    research_allowed_tools,
)


def test_research_forbids_side_effecting_tools() -> None:
    assert_research_readonly(["retrieve", "rerank"])
    with pytest.raises(SideEffectToolError):
        assert_research_readonly(["retrieve", "delete_document"])
    assert "retrieve" in research_allowed_tools()
    assert "write_file" not in research_allowed_tools()
