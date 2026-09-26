"""
File: permissions.py
Description: Permission model: read / write / manage and mapped actions (FR-ACL-02)
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

from enum import IntEnum, StrEnum


class Permission(IntEnum):
    """Ordered permission levels; higher includes lower."""

    READ = 1
    WRITE = 2
    MANAGE = 3


class Action(StrEnum):
    QUERY = "query"
    VIEW = "view"
    DOWNLOAD = "download"
    UPLOAD = "upload"
    EDIT_METADATA = "edit_metadata"
    MANAGE_ACL = "manage_acl"
    DELETE = "delete"


_ACTION_PERMISSION: dict[Action, Permission] = {
    Action.QUERY: Permission.READ,
    Action.VIEW: Permission.READ,
    Action.DOWNLOAD: Permission.READ,
    Action.UPLOAD: Permission.WRITE,
    Action.EDIT_METADATA: Permission.WRITE,
    Action.MANAGE_ACL: Permission.MANAGE,
    Action.DELETE: Permission.MANAGE,
}


def permission_for_action(action: Action) -> Permission:
    return _ACTION_PERMISSION[action]


def allows(granted: Permission, action: Action) -> bool:
    """Return True if the granted permission covers the action."""
    return granted >= permission_for_action(action)
