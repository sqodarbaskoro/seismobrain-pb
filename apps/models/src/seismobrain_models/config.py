"""
File: config.py
Description: Models service settings with CPU-only default (NFR-PORT-02)
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

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def default_device(*, tier: str = "starter") -> Literal["cpu"]:
    _ = tier
    return "cpu"


class ModelsSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SB_MODELS_", extra="ignore")

    device: Literal["cpu"] = Field(default_factory=lambda: default_device())
    allow_gpu: bool = False
    embed_dim: int = 32
