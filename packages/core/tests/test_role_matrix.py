"""
File: test_role_matrix.py
Description: System/workspace role matrix tests per PRD §13.3 (FR-AUTH-04)
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

from seismobrain_core.roles import (
    RoleAction,
    SystemRole,
    WorkspaceRole,
    role_allows,
)


@pytest.mark.parametrize("role", list(WorkspaceRole))
def test_all_workspace_roles_can_ask_view_download_and_feedback(
    role: WorkspaceRole,
) -> None:
    for action in (
        RoleAction.ASK_VIEW_DOWNLOAD,
        RoleAction.GIVE_FEEDBACK,
    ):
        assert (
            role_allows(
                system_role=SystemRole.USER,
                workspace_role=role,
                action=action,
            )
            is True
        )


def test_upload_requires_write_grant_for_member() -> None:
    assert (
        role_allows(
            system_role=SystemRole.USER,
            workspace_role=WorkspaceRole.MEMBER,
            action=RoleAction.UPLOAD_EDIT_METADATA,
            collection_grants_write=False,
        )
        is False
    )
    assert (
        role_allows(
            system_role=SystemRole.USER,
            workspace_role=WorkspaceRole.MEMBER,
            action=RoleAction.UPLOAD_EDIT_METADATA,
            collection_grants_write=True,
        )
        is True
    )
    assert (
        role_allows(
            system_role=SystemRole.USER,
            workspace_role=WorkspaceRole.VIEWER,
            action=RoleAction.UPLOAD_EDIT_METADATA,
            collection_grants_write=True,
        )
        is False
    )


@pytest.mark.parametrize(
    ("role", "action", "expected"),
    [
        (WorkspaceRole.VIEWER, RoleAction.UPLOAD_EDIT_METADATA, False),
        (WorkspaceRole.MEMBER, RoleAction.FOLDER_INGESTION_GLOSSARY_EVAL, False),
        (WorkspaceRole.CURATOR, RoleAction.UPLOAD_EDIT_METADATA, True),
        (WorkspaceRole.CURATOR, RoleAction.FOLDER_INGESTION_GLOSSARY_EVAL, True),
        (WorkspaceRole.CURATOR, RoleAction.COLLECTION_ACL_WORKSPACE_SETTINGS, False),
        (WorkspaceRole.OWNER, RoleAction.COLLECTION_ACL_WORKSPACE_SETTINGS, True),
        (WorkspaceRole.OWNER, RoleAction.SYSTEM_CONFIGURATION, False),
        (WorkspaceRole.OWNER, RoleAction.FOLDER_INGESTION_GLOSSARY_EVAL, True),
    ],
)
def test_workspace_role_matrix_cells(
    role: WorkspaceRole, action: RoleAction, expected: bool
) -> None:
    assert (
        role_allows(
            system_role=SystemRole.USER,
            workspace_role=role,
            action=action,
            collection_grants_write=True,
        )
        is expected
    )


def test_system_admin_allows_all_actions() -> None:
    for action in RoleAction:
        assert (
            role_allows(
                system_role=SystemRole.SYSTEM_ADMIN,
                workspace_role=None,
                action=action,
            )
            is True
        )


def test_system_roles_are_defined() -> None:
    assert set(SystemRole) == {SystemRole.SYSTEM_ADMIN, SystemRole.USER}
    assert set(WorkspaceRole) == {
        WorkspaceRole.OWNER,
        WorkspaceRole.CURATOR,
        WorkspaceRole.MEMBER,
        WorkspaceRole.VIEWER,
    }
