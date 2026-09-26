"""
File: test_model_pinning.py
Description: Model artifacts pinned revisions + checksum (T4.18)
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
from pathlib import Path

import pytest

from seismobrain_models.pinning import (
    ModelPin,
    ModelPinningError,
    load_pinned_artifact,
    sha256_file,
)


def test_pinned_revision_checksum_and_no_remote_code(tmp_path: Path) -> None:
    artifact = tmp_path / "embed.bin"
    artifact.write_bytes(b"model-bytes")
    (tmp_path / "embed.bin.pin").write_text("rev-abc", encoding="utf-8")
    digest = sha256_file(artifact)
    pin = ModelPin(name="embed", revision="rev-abc", sha256=digest)

    loaded = load_pinned_artifact(artifact, pin, trust_remote_code=False)
    assert loaded == b"model-bytes"

    with pytest.raises(ModelPinningError, match="remote code"):
        load_pinned_artifact(artifact, pin, trust_remote_code=True)

    bad = ModelPin(name="embed", revision="rev-abc", sha256=hashlib.sha256(b"x").hexdigest())
    with pytest.raises(ModelPinningError, match="checksum"):
        load_pinned_artifact(artifact, bad)

    (tmp_path / "embed.bin.pin").write_text("other", encoding="utf-8")
    with pytest.raises(ModelPinningError, match="revision"):
        load_pinned_artifact(artifact, pin)
