"""
File: test_bulk_ingest.py
Description: Bulk ingestion resumable lower priority (T5.16)
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

from seismobrain_ingest.bulk_ingest import BulkIngestRun


def test_bulk_mode_resumes_after_restart() -> None:
    run = BulkIngestRun(run_id="bulk-1", files=["a.pdf", "b.pdf", "c.pdf"])
    assert run.priority == "low"
    assert run.process_next() == "a.pdf"
    resumed = run.resume_after_restart()
    assert resumed.cursor == 1
    assert resumed.process_next() == "b.pdf"
    stats = resumed.throughput()
    assert stats["completed"] == 2
    assert stats["remaining"] == 1
