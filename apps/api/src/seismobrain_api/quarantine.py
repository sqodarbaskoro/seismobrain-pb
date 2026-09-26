"""
File: quarantine.py
Description: Quarantine store for failed validation/encryption/malware (FR-ING-06)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-17
Version: 0.2.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field


@dataclass
class QuarantineItem:
    id: str
    filename: str
    reason: str
    status: str = "quarantined"
    created_at: float = field(default_factory=time.time)


@dataclass
class QuarantineStore:
    items: dict[str, QuarantineItem] = field(default_factory=dict)

    def quarantine(self, *, filename: str, reason: str) -> QuarantineItem:
        item = QuarantineItem(id=f"q_{uuid.uuid4().hex[:10]}", filename=filename, reason=reason)
        self.items[item.id] = item
        return item

    def inspect(self, item_id: str) -> QuarantineItem:
        return self.items[item_id]

    def list_pending(self) -> list[QuarantineItem]:
        return sorted(
            (item for item in self.items.values() if item.status == "quarantined"),
            key=lambda item: item.created_at,
        )

    def release(self, item_id: str, *, actor: str) -> QuarantineItem:
        _ = actor
        item = self.items[item_id]
        item.status = "released"
        return item
