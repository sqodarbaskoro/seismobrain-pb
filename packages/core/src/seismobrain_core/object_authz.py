"""
File: object_authz.py
Description: Object-level ownership checks for resource identifiers (SEC-12)
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


class ResourceType(StrEnum):
    CONVERSATION = "conversation"
    MESSAGE = "message"
    DOCUMENT = "document"
    JOB = "job"
    EVIDENCE = "evidence"


class ObjectAccessError(Exception):
    """Raised when the caller may not access the identified object."""


@dataclass
class ObjectOwnershipStore:
    """Maps resource identifiers to owning user IDs."""

    _owners: dict[tuple[ResourceType, str], str] = field(default_factory=dict)

    def put(
        self, *, resource_type: ResourceType, resource_id: str, owner_user_id: str
    ) -> None:
        self._owners[(resource_type, resource_id)] = owner_user_id

    def owner_of(
        self, *, resource_type: ResourceType, resource_id: str
    ) -> str | None:
        return self._owners.get((resource_type, resource_id))


def require_object_access(
    *,
    actor_user_id: str,
    resource_type: ResourceType,
    resource_id: str,
    store: ObjectOwnershipStore,
) -> None:
    owner = store.owner_of(resource_type=resource_type, resource_id=resource_id)
    if owner is None:
        raise ObjectAccessError("not found")
    if owner != actor_user_id:
        raise ObjectAccessError("forbidden")
