"""
File: test_permissions.py
Description: Permission model tests for read/write/manage (FR-ACL-02)
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

from seismobrain_core.permissions import (
    Action,
    Permission,
    allows,
    permission_for_action,
)


def test_permission_actions_mapping() -> None:
    assert permission_for_action(Action.QUERY) == Permission.READ
    assert permission_for_action(Action.VIEW) == Permission.READ
    assert permission_for_action(Action.DOWNLOAD) == Permission.READ
    assert permission_for_action(Action.UPLOAD) == Permission.WRITE
    assert permission_for_action(Action.EDIT_METADATA) == Permission.WRITE
    assert permission_for_action(Action.MANAGE_ACL) == Permission.MANAGE
    assert permission_for_action(Action.DELETE) == Permission.MANAGE


@pytest.mark.parametrize(
    ("granted", "action", "expected"),
    [
        (Permission.READ, Action.QUERY, True),
        (Permission.READ, Action.VIEW, True),
        (Permission.READ, Action.DOWNLOAD, True),
        (Permission.READ, Action.UPLOAD, False),
        (Permission.READ, Action.DELETE, False),
        (Permission.WRITE, Action.UPLOAD, True),
        (Permission.WRITE, Action.EDIT_METADATA, True),
        (Permission.WRITE, Action.QUERY, True),  # write implies read
        (Permission.WRITE, Action.MANAGE_ACL, False),
        (Permission.MANAGE, Action.MANAGE_ACL, True),
        (Permission.MANAGE, Action.DELETE, True),
        (Permission.MANAGE, Action.UPLOAD, True),
        (Permission.MANAGE, Action.DOWNLOAD, True),
    ],
)
def test_allows_permission_hierarchy(
    granted: Permission, action: Action, expected: bool
) -> None:
    assert allows(granted, action) is expected
