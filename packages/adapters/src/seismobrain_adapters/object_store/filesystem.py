"""
File: filesystem.py
Description: Filesystem ObjectStore adapter for Starter/Team volume storage
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-26
Version: 0.1.1
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

from pathlib import Path


class FilesystemObjectStore:
    """ObjectStore that writes opaque blobs under a root directory."""

    def __init__(self, root: Path | str) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        cleaned = key.lstrip("/")
        path = (self._root / cleaned).resolve()
        if not path.is_relative_to(self._root.resolve()):
            raise ValueError("key escapes object store root")
        return path

    def put(self, key: str, data: bytes) -> None:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def get(self, key: str) -> bytes:
        path = self._resolve(key)
        if not path.is_file():
            raise KeyError(key)
        return path.read_bytes()

    def delete(self, key: str) -> None:
        path = self._resolve(key)
        if path.is_file():
            path.unlink()

    def exists(self, key: str) -> bool:
        return self._resolve(key).is_file()

    def list_keys(self, prefix: str = "") -> list[str]:
        root = self._root.resolve()
        cleaned = prefix.lstrip("/")
        base = (root / cleaned) if cleaned else root
        if base.is_file():
            return [cleaned]
        if not base.exists():
            return []
        keys: list[str] = []
        for path in base.rglob("*"):
            if path.is_file():
                keys.append(str(path.relative_to(root)).replace("\\", "/"))
        return sorted(keys)
