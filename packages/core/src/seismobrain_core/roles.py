"""
File: roles.py
Description: System and workspace roles with §13.3 role matrix (FR-AUTH-04)
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

from enum import StrEnum


class SystemRole(StrEnum):
    SYSTEM_ADMIN = "system_admin"
    USER = "user"


class WorkspaceRole(StrEnum):
    OWNER = "owner"
    CURATOR = "curator"
    MEMBER = "member"
    VIEWER = "viewer"


class RoleAction(StrEnum):
    """Rows from PRD §13.3 role matrix."""

    ASK_VIEW_DOWNLOAD = "ask_view_download"
    GIVE_FEEDBACK = "give_feedback"
    UPLOAD_EDIT_METADATA = "upload_edit_metadata"
    FOLDER_INGESTION_GLOSSARY_EVAL = "folder_ingestion_glossary_eval"
    COLLECTION_ACL_WORKSPACE_SETTINGS = "collection_acl_workspace_settings"
    SYSTEM_CONFIGURATION = "system_configuration"


_MATRIX: dict[WorkspaceRole, frozenset[RoleAction]] = {
    WorkspaceRole.VIEWER: frozenset(
        {RoleAction.ASK_VIEW_DOWNLOAD, RoleAction.GIVE_FEEDBACK}
    ),
    WorkspaceRole.MEMBER: frozenset(
        {
            RoleAction.ASK_VIEW_DOWNLOAD,
            RoleAction.GIVE_FEEDBACK,
            RoleAction.UPLOAD_EDIT_METADATA,
        }
    ),
    WorkspaceRole.CURATOR: frozenset(
        {
            RoleAction.ASK_VIEW_DOWNLOAD,
            RoleAction.GIVE_FEEDBACK,
            RoleAction.UPLOAD_EDIT_METADATA,
            RoleAction.FOLDER_INGESTION_GLOSSARY_EVAL,
        }
    ),
    WorkspaceRole.OWNER: frozenset(
        {
            RoleAction.ASK_VIEW_DOWNLOAD,
            RoleAction.GIVE_FEEDBACK,
            RoleAction.UPLOAD_EDIT_METADATA,
            RoleAction.FOLDER_INGESTION_GLOSSARY_EVAL,
            RoleAction.COLLECTION_ACL_WORKSPACE_SETTINGS,
        }
    ),
}


def role_allows(
    *,
    system_role: SystemRole,
    workspace_role: WorkspaceRole | None,
    action: RoleAction,
    collection_grants_write: bool = False,
) -> bool:
    """Return whether the role combination may perform the matrix action."""
    if system_role is SystemRole.SYSTEM_ADMIN:
        return True
    if workspace_role is None:
        return False
    if action not in _MATRIX[workspace_role]:
        return False
    if (
        action is RoleAction.UPLOAD_EDIT_METADATA
        and workspace_role is WorkspaceRole.MEMBER
        and not collection_grants_write
    ):
        return False
    return True
