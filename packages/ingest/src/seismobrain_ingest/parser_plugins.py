"""
File: parser_plugins.py
Description: Parser plug-in registry so formats can be added without core changes
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

from pathlib import PurePosixPath
from typing import Protocol

from seismobrain_ingest.document_tree import DocumentTree


class ParserPlugin(Protocol):
    """Plug-in that parses one or more file formats into a DocumentTree."""

    @property
    def formats(self) -> frozenset[str]:
        """Lowercase extensions without dot, e.g. frozenset({'html'})."""

    def parse(self, filename: str, data: bytes) -> DocumentTree:
        """Parse file bytes into a DocumentTree."""


class ParserRegistry:
    """Dispatches parsing by extension; new formats register without core edits."""

    def __init__(self) -> None:
        self._plugins: dict[str, ParserPlugin] = {}

    def register(self, plugin: ParserPlugin) -> None:
        for fmt in plugin.formats:
            key = fmt.lower().lstrip(".")
            self._plugins[key] = plugin

    def supports(self, filename: str) -> bool:
        return self._extension(filename) in self._plugins

    def parse(self, filename: str, data: bytes) -> DocumentTree:
        fmt = self._extension(filename)
        plugin = self._plugins.get(fmt)
        if plugin is None:
            raise KeyError(f"no parser registered for format: {fmt or '(none)'}")
        return plugin.parse(filename, data)

    @staticmethod
    def _extension(filename: str) -> str:
        return PurePosixPath(filename).suffix.lower().lstrip(".")
