"""
File: test_starter_bind.py
Description: Starter tier bind-host default and exposure warning (SEC-22)
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

from unittest.mock import patch

import pytest

from seismobrain_api.config import Settings
from seismobrain_api.starter_bind import warn_if_starter_exposed


def test_starter_defaults_to_loopback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)
    monkeypatch.setenv("SB_TIER", "starter")
    settings = Settings()  # type: ignore[call-arg]
    assert settings.bind_host == "127.0.0.1"
    assert warn_if_starter_exposed(settings) is None


def test_starter_warns_when_bound_broadly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("MASTER_KEY", "b" * 64)
    monkeypatch.setenv("SB_TIER", "starter")
    monkeypatch.setenv("BIND_HOST", "0.0.0.0")
    settings = Settings()  # type: ignore[call-arg]
    with patch("seismobrain_api.starter_bind._LOG.warning") as warning:
        message = warn_if_starter_exposed(settings)
    assert message is not None
    assert "0.0.0.0" in message
    assert "exposed" in message.lower()
    warning.assert_called_once()
    assert "exposed" in warning.call_args.args[0].lower()
