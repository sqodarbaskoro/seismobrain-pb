"""
File: principal_epoch.py
Description: Principal authorization epoch bumping without touching document ACLs
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

from dataclasses import dataclass, replace


@dataclass(frozen=True, slots=True)
class PrincipalSet:
    user_id: str
    group_ids: frozenset[str]
    epoch: int


def bump_principal_authz_epochs(
    users: dict[str, PrincipalSet],
    *,
    changed_group_id: str | None = None,
    changed_user_id: str | None = None,
) -> dict[str, PrincipalSet]:
    """
    Increment principal_authz_epoch for affected users only.

    Does not modify document/collection ACL epochs (FR-ACL-12).
    """
    out = dict(users)
    if changed_user_id is not None and changed_user_id in out:
        current = out[changed_user_id]
        out[changed_user_id] = replace(current, epoch=current.epoch + 1)
    if changed_group_id is not None:
        for user_id, principal in list(out.items()):
            if changed_group_id in principal.group_ids:
                out[user_id] = replace(principal, epoch=principal.epoch + 1)
    return out
