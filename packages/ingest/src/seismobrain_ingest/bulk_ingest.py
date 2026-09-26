"""
File: bulk_ingest.py
Description: Bulk ingestion mode — resumable, lower priority (FR-ING-09)
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

from dataclasses import dataclass, field


@dataclass
class BulkIngestRun:
    run_id: str
    files: list[str]
    cursor: int = 0
    priority: str = "low"
    completed: list[str] = field(default_factory=list)

    def process_next(self) -> str | None:
        if self.cursor >= len(self.files):
            return None
        name = self.files[self.cursor]
        self.cursor += 1
        self.completed.append(name)
        return name

    def resume_after_restart(self) -> BulkIngestRun:
        """Return state that continues from cursor (idempotent resume)."""
        return BulkIngestRun(
            run_id=self.run_id,
            files=list(self.files),
            cursor=self.cursor,
            priority=self.priority,
            completed=list(self.completed),
        )

    def throughput(self) -> dict[str, float | int | str]:
        return {
            "completed": len(self.completed),
            "remaining": max(0, len(self.files) - self.cursor),
            "priority": self.priority,
        }
