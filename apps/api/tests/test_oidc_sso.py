"""
File: test_oidc_sso.py
Description: OIDC SSO with group-claim mapping (T4.3)
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

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from seismobrain_adapters.authz.deny import DenyAllAuthorizationGuard
from seismobrain_adapters.event_log.in_memory import InMemoryEventLog
from seismobrain_adapters.metadata.sqlite import SqliteMetadataStore
from seismobrain_adapters.object_store.filesystem import FilesystemObjectStore
from seismobrain_adapters.queue.in_process import InProcessJobQueue
from seismobrain_adapters.rate_limit.in_memory import InMemoryRateLimiter
from seismobrain_api.app import create_app
from seismobrain_api.auth.oidc import MockOidcProvider, OidcService, OidcSettings
from seismobrain_api.auth.users import InMemoryUserStore
from seismobrain_api.config import Settings
from seismobrain_api.container import AppContainer


@pytest.fixture
def container(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> AppContainer:
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)
    monkeypatch.setenv("SB_TIER", "starter")
    provider = MockOidcProvider(
        tokens={
            "good": {"sub": "u-oidc", "groups": ["Engineering"]},
        }
    )
    return AppContainer(
        settings=Settings(),  # type: ignore[call-arg]
        metadata_store=SqliteMetadataStore(tmp_path / "meta.db"),
        job_queue=InProcessJobQueue(tmp_path / "jobs"),
        object_store=FilesystemObjectStore(tmp_path / "objects"),
        event_log=InMemoryEventLog(),
        rate_limiter=InMemoryRateLimiter(),
        authorization_guard=DenyAllAuthorizationGuard(),
        user_store=InMemoryUserStore(),
        oidc=OidcService(
            settings=OidcSettings(local_login_disabled=True),
            verifier=provider,
            group_map={"Engineering": "grp_eng"},
        ),
    )


def test_oidc_group_claim_mapping_and_local_login_disabled(
    container: AppContainer,
) -> None:
    client = TestClient(create_app(container))
    assert client.get("/api/v1/auth/oidc/local-login").json()["allowed"] is False
    ok = client.post("/api/v1/auth/oidc/login", json={"id_token": "good"})
    assert ok.status_code == 200
    body = ok.json()
    assert body["user_id"] == "u-oidc"
    assert body["groups"] == ["grp_eng"]
    bad = client.post("/api/v1/auth/oidc/login", json={"id_token": "nope"})
    assert bad.status_code == 401
