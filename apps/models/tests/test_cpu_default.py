"""
File: test_cpu_default.py
Description: Starter models default to CPU-only operation (NFR-PORT-02 / T0c.8)
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

from seismobrain_models.config import ModelsSettings, default_device


def test_starter_defaults_to_cpu() -> None:
    settings = ModelsSettings()
    assert settings.device == "cpu"
    assert default_device(tier="starter") == "cpu"
    assert default_device(tier="team") == "cpu"
    assert settings.allow_gpu is False
