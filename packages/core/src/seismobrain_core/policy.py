"""
File: policy.py
Description: Central route policy registry with default deny (SEC-05)
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

from dataclasses import dataclass, field
from enum import StrEnum

from seismobrain_core.roles import RoleAction, SystemRole, WorkspaceRole, role_allows


class PolicyDecision(StrEnum):
    ALLOW = "allow"
    DENY = "deny"


@dataclass(frozen=True)
class RoutePermission:
    method: str
    path: str
    action: RoleAction
    public: bool = False

    @property
    def key(self) -> tuple[str, str]:
        return (self.method.upper(), self.path)


@dataclass
class PolicyRegistry:
    """Every route must declare its permission; missing entries deny."""

    _routes: dict[tuple[str, str], RoutePermission] = field(default_factory=dict)

    def declare(self, route: RoutePermission) -> None:
        if route.key in self._routes:
            raise ValueError(f"route already declared: {route.method} {route.path}")
        self._routes[route.key] = route

    def get(self, method: str, path: str) -> RoutePermission | None:
        return self._routes.get((method.upper(), path))


def authorize_route(
    registry: PolicyRegistry,
    *,
    method: str,
    path: str,
    system_role: SystemRole | None,
    workspace_role: WorkspaceRole | None,
    collection_grants_write: bool = False,
) -> PolicyDecision:
    route = registry.get(method, path)
    if route is None:
        return PolicyDecision.DENY
    if route.public:
        return PolicyDecision.ALLOW
    if system_role is None:
        return PolicyDecision.DENY
    allowed = role_allows(
        system_role=system_role,
        workspace_role=workspace_role,
        action=route.action,
        collection_grants_write=collection_grants_write,
    )
    return PolicyDecision.ALLOW if allowed else PolicyDecision.DENY
