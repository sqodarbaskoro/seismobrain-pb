"""
File: test_policy_default_deny.py
Description: Central policy module default-deny tests (SEC-05)
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

from seismobrain_core.policy import (
    PolicyDecision,
    PolicyRegistry,
    RoutePermission,
    authorize_route,
)
from seismobrain_core.roles import RoleAction, SystemRole, WorkspaceRole


def test_undeclared_route_is_denied() -> None:
    registry = PolicyRegistry()
    decision = authorize_route(
        registry,
        method="GET",
        path="/secret",
        system_role=SystemRole.SYSTEM_ADMIN,
        workspace_role=WorkspaceRole.OWNER,
    )
    assert decision is PolicyDecision.DENY


def test_declared_route_uses_role_matrix() -> None:
    registry = PolicyRegistry()
    registry.declare(
        RoutePermission(
            method="POST",
            path="/documents",
            action=RoleAction.UPLOAD_EDIT_METADATA,
        )
    )
    assert (
        authorize_route(
            registry,
            method="POST",
            path="/documents",
            system_role=SystemRole.USER,
            workspace_role=WorkspaceRole.VIEWER,
            collection_grants_write=True,
        )
        is PolicyDecision.DENY
    )
    assert (
        authorize_route(
            registry,
            method="POST",
            path="/documents",
            system_role=SystemRole.USER,
            workspace_role=WorkspaceRole.CURATOR,
            collection_grants_write=True,
        )
        is PolicyDecision.ALLOW
    )


def test_declare_duplicate_raises() -> None:
    registry = PolicyRegistry()
    route = RoutePermission(
        method="GET",
        path="/health",
        action=RoleAction.ASK_VIEW_DOWNLOAD,
        public=True,
    )
    registry.declare(route)
    with pytest.raises(ValueError, match="already declared"):
        registry.declare(route)


def test_public_route_allows_anonymous() -> None:
    registry = PolicyRegistry()
    registry.declare(
        RoutePermission(
            method="GET",
            path="/health",
            action=RoleAction.ASK_VIEW_DOWNLOAD,
            public=True,
        )
    )
    assert (
        authorize_route(
            registry,
            method="GET",
            path="/health",
            system_role=None,
            workspace_role=None,
        )
        is PolicyDecision.ALLOW
    )
