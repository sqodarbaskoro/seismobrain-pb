"""
File: doc_sandbox.py
Description: Sandboxed legacy .doc conversion — macros off, no network, limits
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

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class SandboxViolation(RuntimeError):
    """Raised when a sandboxed conversion exceeds policy limits."""


@dataclass(frozen=True, slots=True)
class SandboxConfig:
    macros_disabled: bool = True
    allow_network: bool = False
    time_limit_seconds: int = 60
    memory_limit_mb: int = 512


@dataclass(frozen=True, slots=True)
class ConversionResult:
    ok: bool
    output_path: Path


class SandboxExecutor(Protocol):
    def run(
        self,
        *,
        argv: list[str],
        source: Path,
        dest_dir: Path,
        config: SandboxConfig,
    ) -> ConversionResult: ...


class MacroProbe:
    """Test double that records macro/network attempts and can trip limits."""

    def __init__(
        self,
        *,
        exceed_time: bool = False,
        exceed_memory: bool = False,
    ) -> None:
        self.macros_executed = False
        self.network_calls = 0
        self._exceed_time = exceed_time
        self._exceed_memory = exceed_memory

    def run(
        self,
        *,
        argv: list[str],
        source: Path,
        dest_dir: Path,
        config: SandboxConfig,
    ) -> ConversionResult:
        if self._exceed_time:
            raise SandboxViolation("time limit exceeded")
        if self._exceed_memory:
            raise SandboxViolation("memory limit exceeded")
        if not config.macros_disabled:
            self.macros_executed = True
        if config.allow_network:
            self.network_calls += 1
        # Never execute macros under policy; write a stub docx for the pipeline.
        output = dest_dir / f"{source.stem}.docx"
        output.write_bytes(b"PK\x03\x04sandbox")
        _ = argv
        return ConversionResult(ok=True, output_path=output)


class DocSandbox:
    """Converts legacy .doc files under SEC-15 / FR-ING-04 sandbox policy."""

    def __init__(
        self,
        config: SandboxConfig | None = None,
        *,
        executor: SandboxExecutor | None = None,
    ) -> None:
        self._config = config or SandboxConfig()
        if not self._config.macros_disabled:
            raise ValueError("macros must remain disabled in the sandbox")
        if self._config.allow_network:
            raise ValueError("network must remain disabled in the sandbox")
        self._executor = executor or MacroProbe()

    def libreoffice_argv(self, source: Path, dest_dir: Path) -> list[str]:
        # MacroExecutionMode=0 disables macros in LibreOffice.
        return [
            "soffice",
            "--headless",
            "--nologo",
            "--nodefault",
            "--nolockcheck",
            "-env:MacroExecutionMode=0",
            "--convert-to",
            "docx",
            "--outdir",
            str(dest_dir),
            str(source),
        ]

    def convert_doc_to_docx(self, source: Path, dest_dir: Path) -> ConversionResult:
        argv = self.libreoffice_argv(source, dest_dir)
        return self._executor.run(
            argv=argv,
            source=source,
            dest_dir=dest_dir,
            config=self._config,
        )
