"""
File: test_typed_refusals.py
Description: Typed refusals with distinct messages (T3.8)
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

from seismobrain_core.typed_refusals import RefusalType, distinct_messages, make_refusal


def test_all_refusal_types_have_distinct_messages() -> None:
    msgs = distinct_messages()
    assert set(msgs) == {t.value for t in RefusalType}
    assert len(set(msgs.values())) == len(msgs)
    blocked = make_refusal(RefusalType.POLICY_BLOCKED, policy_name="local_only")
    assert "local_only" in blocked.message
