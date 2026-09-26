"""
File: test_doc_sandbox.py
Description: SEC-15 / FR-ING-04 — doc conversion sandbox: no macros, no network, limits
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

from pathlib import Path

import pytest

from seismobrain_ingest.doc_sandbox import (
    DocSandbox,
    MacroProbe,
    SandboxConfig,
    SandboxViolation,
)


def test_sandbox_config_disables_macros_and_network() -> None:
    config = SandboxConfig()
    assert config.macros_disabled is True
    assert config.allow_network is False
    assert config.time_limit_seconds > 0
    assert config.memory_limit_mb > 0
    argv = DocSandbox(config).libreoffice_argv(Path("in.doc"), Path("out"))
    joined = " ".join(argv)
    assert "--headless" in argv
    assert "macro" in joined.lower() or "MacroExecutionMode" in joined
    assert config.macros_disabled


def test_macro_sample_does_not_execute(tmp_path: Path) -> None:
    probe = MacroProbe()
    sandbox = DocSandbox(SandboxConfig(), executor=probe)
    source = tmp_path / "macro.doc"
    source.write_bytes(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"MACRO")
    dest_dir = tmp_path / "out"
    dest_dir.mkdir()
    result = sandbox.convert_doc_to_docx(source, dest_dir)
    assert result.ok is True
    assert probe.macros_executed is False
    assert probe.network_calls == 0
    assert (dest_dir / "macro.docx").exists()


def test_sandbox_enforces_time_and_memory_limits() -> None:
    sandbox = DocSandbox(
        SandboxConfig(time_limit_seconds=1, memory_limit_mb=64),
        executor=MacroProbe(exceed_time=True),
    )
    with pytest.raises(SandboxViolation, match="time"):
        sandbox.convert_doc_to_docx(Path("in.doc"), Path("out"))

    sandbox = DocSandbox(
        SandboxConfig(time_limit_seconds=30, memory_limit_mb=16),
        executor=MacroProbe(exceed_memory=True),
    )
    with pytest.raises(SandboxViolation, match="memory"):
        sandbox.convert_doc_to_docx(Path("in.doc"), Path("out"))
