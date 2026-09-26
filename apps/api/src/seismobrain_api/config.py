"""
File: config.py
Description: Startup settings validation for the API (pydantic-settings; not in core)
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

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated runtime configuration loaded at process start."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    jwt_secret: str = Field(alias="JWT_SECRET")
    master_key: str = Field(alias="MASTER_KEY")
    sb_tier: Literal["starter", "team", "production"] = Field(
        default="starter", alias="SB_TIER"
    )
    environment: Literal["development", "production", "test"] = Field(
        default="development", alias="ENVIRONMENT"
    )
    registration_mode: Literal["approval", "closed", "open"] = Field(
        default="approval", alias="REGISTRATION_MODE"
    )
    access_token_ttl_min: int = Field(default=15, alias="ACCESS_TOKEN_TTL_MIN", le=15, ge=1)
    refresh_token_ttl_days: int = Field(default=7, alias="REFRESH_TOKEN_TTL_DAYS", ge=1)
    auth_rate_limit_per_min: int = Field(default=10, alias="AUTH_RATE_LIMIT_PER_MIN", ge=1)
    chat_rate_limit_per_min: int = Field(default=30, alias="CHAT_RATE_LIMIT_PER_MIN", ge=1)
    upload_rate_limit_per_hour: int = Field(
        default=60, alias="UPLOAD_RATE_LIMIT_PER_HOUR", ge=1
    )
    bind_host: str = Field(default="127.0.0.1", alias="BIND_HOST")
    public_url: str = Field(default="http://127.0.0.1:8080", alias="PUBLIC_URL")
    upload_max_bytes: int = Field(
        default=200 * 1024 * 1024, alias="UPLOAD_MAX_BYTES", ge=1
    )
    air_gapped: bool = Field(default=False, alias="AIR_GAPPED")

    @field_validator("jwt_secret", "master_key")
    @classmethod
    def _require_strong_secret(cls, value: str) -> str:
        if len(value) < 64:
            raise ValueError(
                "secret must be at least 64 characters "
                "(generate with npm run setup / openssl rand -hex 32)"
            )
        return value


def load_settings() -> Settings:
    """Load and validate settings; raises ValidationError on weak/missing secrets."""
    return Settings()  # type: ignore[call-arg]
