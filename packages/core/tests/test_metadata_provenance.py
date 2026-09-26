"""
File: test_metadata_provenance.py
Description: Metadata value source and confidence (T5.21)
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

from seismobrain_core.metadata_provenance import MetadataSource, record_metadata_value


def test_metadata_records_source_and_confidence() -> None:
    value = record_metadata_value(
        "OPS-204", source=MetadataSource.DOCUMENT_CONTROL, confidence=0.95
    )
    assert value.source is MetadataSource.DOCUMENT_CONTROL
    assert value.confidence == 0.95
