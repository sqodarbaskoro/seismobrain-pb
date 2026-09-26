"""
File: test_document_control_extraction.py
Description: Document-control extraction accuracy (T5.14)
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

from seismobrain_ingest.document_control import (
    DocumentControlFields,
    extract_document_control,
    field_accuracy,
)


def test_document_control_accuracy_on_sample() -> None:
    text = """
    Title: Pump Seal Procedure
    Document Number: OPS-204
    Revision: B
    Date: 2024-06-01
    Author: Alice Smith
    """
    predicted = extract_document_control(text)
    gold = DocumentControlFields(
        title="Pump Seal Procedure",
        document_number="OPS-204",
        revision="B",
        date="2024-06-01",
        author="Alice Smith",
    )
    assert field_accuracy(predicted, gold) >= 0.9
