"""
File: document_versioning.py
Description: Document versioning by logical key (FR-DOC-04)
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

import uuid
from dataclasses import dataclass, field


@dataclass
class DocumentVersionIndex:
    _by_key: dict[str, str] = field(default_factory=dict)
    _versions: dict[str, list[str]] = field(default_factory=dict)

    def register(self, *, logical_key: str, version_id: str) -> str:
        if logical_key not in self._by_key:
            self._by_key[logical_key] = f"doc_{uuid.uuid4().hex[:8]}"
            self._versions[logical_key] = []
        self._versions[logical_key].append(version_id)
        return self._by_key[logical_key]

    def document_id(self, logical_key: str) -> str:
        return self._by_key[logical_key]

    def latest(self, logical_key: str) -> str:
        return self._versions[logical_key][-1]

    def history(self, logical_key: str) -> list[str]:
        return list(self._versions[logical_key])
