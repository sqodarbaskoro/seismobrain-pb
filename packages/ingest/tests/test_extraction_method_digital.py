"""
File: test_extraction_method_digital.py
Description: FR-ING-07 — digital extraction_method and quality score on chunks
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

from seismobrain_ingest.extraction_method import digital_extraction_meta


def test_digital_extraction_records_method_and_quality() -> None:
    meta = digital_extraction_meta("c1", text="Hello calibration procedure.")
    assert meta.extraction_method == "digital"
    assert meta.chunk_id == "c1"
    assert 0.0 < meta.quality_score <= 1.0

    poor = digital_extraction_meta("c2", text="\x00\x01\x02abc")
    assert poor.extraction_method == "digital"
    assert poor.quality_score < meta.quality_score
