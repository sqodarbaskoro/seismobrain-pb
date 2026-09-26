"""
File: test_config_validation.py
Description: Startup configuration validation lives in apps/api, not packages/core
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
from pydantic import ValidationError

from seismobrain_api.config import load_settings


def test_settings_require_strong_jwt_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("JWT_SECRET", raising=False)
    monkeypatch.setenv("JWT_SECRET", "short")
    with pytest.raises(ValidationError):
        load_settings()


def test_settings_accept_hex_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    secret = "a" * 64
    monkeypatch.setenv("JWT_SECRET", secret)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)
    monkeypatch.setenv("SB_TIER", "starter")
    settings = load_settings()
    assert settings.jwt_secret == secret
    assert settings.sb_tier == "starter"


def test_core_does_not_use_pydantic_settings_or_environ() -> None:
    """Companion to Verify grep: core must stay env-free."""
    import pathlib
    import re

    core_src = pathlib.Path(__file__).resolve().parents[3] / "packages" / "core" / "src"
    pattern = re.compile(r"pydantic_settings|os\.environ|getenv")
    hits: list[str] = []
    for path in core_src.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if pattern.search(text):
            hits.append(str(path.relative_to(core_src)))
    assert not hits, f"forbidden env/settings usage in core src: {hits}"
