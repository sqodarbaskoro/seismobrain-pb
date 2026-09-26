"""
File: test_package_version.py
Description: Smoke coverage for seismobrain_core package root
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

from seismobrain_core import __version__


def test_version_is_semver_like() -> None:
    assert isinstance(__version__, str)
    assert __version__.count(".") >= 1
