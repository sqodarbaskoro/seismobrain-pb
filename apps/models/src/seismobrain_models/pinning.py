"""
File: pinning.py
Description: Pinned model revisions with checksum verification (SEC-21)
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
from dataclasses import dataclass
from pathlib import Path


class ModelPinningError(ValueError):
    """Raised when pin/checksum/RCE policy checks fail."""


@dataclass(frozen=True, slots=True)
class ModelPin:
    name: str
    revision: str
    sha256: str
    allow_remote_code: bool = False


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_pinned_artifact(
    path: Path,
    pin: ModelPin,
    *,
    trust_remote_code: bool = False,
) -> bytes:
    """Load artifact only when revision pin and checksum match; RCE off by default."""
    if trust_remote_code and not pin.allow_remote_code:
        raise ModelPinningError("remote code execution disabled unless approved")
    if not path.is_file():
        raise ModelPinningError(f"missing artifact: {path}")
    meta = path.with_suffix(path.suffix + ".pin")
    if meta.is_file():
        recorded = meta.read_text(encoding="utf-8").strip()
        if recorded != pin.revision:
            raise ModelPinningError(
                f"revision mismatch: want {pin.revision}, got {recorded}"
            )
    actual = sha256_file(path)
    if actual != pin.sha256:
        raise ModelPinningError("checksum verification failed")
    return path.read_bytes()
