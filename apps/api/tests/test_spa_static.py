"""
File: test_spa_static.py
Description: Starter serves built SPA at / (PRD §16.2)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-17
Modified: 2026-09-17
Version: 0.1.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from seismobrain_api.starter import build_starter_app


def _write_spa(dist: Path) -> None:
    dist.mkdir(parents=True)
    (dist / "index.html").write_text(
        "<!doctype html><html><head><title>SeismoBrain</title></head>"
        '<body><div id="root">ok</div></body></html>\n',
        encoding="utf-8",
    )
    assets = dist / "assets"
    assets.mkdir()
    (assets / "app.js").write_text("window.__SB=1;\n", encoding="utf-8")


def test_starter_serves_spa_index_and_assets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)
    monkeypatch.setenv("SB_TIER", "starter")
    dist = tmp_path / "dist"
    _write_spa(dist)

    client = TestClient(
        build_starter_app(data_dir=tmp_path / "data", spa_dir=dist)
    )

    index = client.get("/")
    assert index.status_code == 200
    assert "text/html" in index.headers["content-type"]
    assert "SeismoBrain" in index.text

    asset = client.get("/assets/app.js")
    assert asset.status_code == 200
    assert "window.__SB=1" in asset.text

    chat = client.get("/chat")
    assert chat.status_code == 200
    assert "SeismoBrain" in chat.text

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    missing_api = client.get("/api/v1/does-not-exist")
    assert missing_api.status_code == 404
    assert "text/html" not in missing_api.headers.get("content-type", "")


def test_starter_requires_spa_dist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)
    monkeypatch.setenv("SB_TIER", "starter")
    with pytest.raises(FileNotFoundError, match="SPA dist"):
        build_starter_app(data_dir=tmp_path / "data", spa_dir=tmp_path / "missing")
