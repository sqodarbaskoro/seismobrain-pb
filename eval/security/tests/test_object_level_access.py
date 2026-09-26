"""
File: test_object_level_access.py
Description: Object-level access denial in security suite (T4.28)
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

from seismobrain_core.object_authz import (
    ObjectAccessError,
    ObjectOwnershipStore,
    ResourceType,
    require_object_access,
)


def test_object_level_access_denies_non_owner() -> None:
    store = ObjectOwnershipStore()
    store.put(
        resource_type=ResourceType.DOCUMENT, resource_id="obj-1", owner_user_id="u1"
    )
    require_object_access(
        actor_user_id="u1",
        resource_type=ResourceType.DOCUMENT,
        resource_id="obj-1",
        store=store,
    )
    with pytest.raises(ObjectAccessError):
        require_object_access(
            actor_user_id="u2",
            resource_type=ResourceType.DOCUMENT,
            resource_id="obj-1",
            store=store,
        )
