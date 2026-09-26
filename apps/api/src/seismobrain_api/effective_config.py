"""
File: effective_config.py
Description: Effective configuration view with sources and hash (FR-ADM-05)
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

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from seismobrain_api.config import Settings


@dataclass(frozen=True, slots=True)
class ConfigEntry:
    key: str
    value: Any
    source: str


def build_effective_config(settings: Settings) -> dict[str, object]:
    entries = [
        ConfigEntry("sb_tier", settings.sb_tier, "env:SB_TIER"),
        ConfigEntry("environment", settings.environment, "env:ENVIRONMENT"),
        ConfigEntry(
            "registration_mode", settings.registration_mode, "env:REGISTRATION_MODE"
        ),
        ConfigEntry(
            "access_token_ttl_min",
            settings.access_token_ttl_min,
            "env:ACCESS_TOKEN_TTL_MIN",
        ),
        ConfigEntry("bind_host", settings.bind_host, "env:BIND_HOST"),
        ConfigEntry("public_url", settings.public_url, "env:PUBLIC_URL"),
        ConfigEntry("air_gapped", settings.air_gapped, "env:AIR_GAPPED"),
        ConfigEntry("upload_max_bytes", settings.upload_max_bytes, "env:UPLOAD_MAX_BYTES"),
    ]
    payload = {e.key: {"value": e.value, "source": e.source} for e in entries}
    canonical = json.dumps(payload, sort_keys=True, default=str)
    return {
        "config": payload,
        "config_hash": hashlib.sha256(canonical.encode()).hexdigest(),
    }
