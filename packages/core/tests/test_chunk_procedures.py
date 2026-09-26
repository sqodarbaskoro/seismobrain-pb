"""
File: test_chunk_procedures.py
Description: FR-CHK-03 — procedure split at steps; warnings stay with step
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

from seismobrain_core.chunking import SectionInput, chunk_document


def test_procedure_steps_keep_title_and_warnings() -> None:
    section = SectionInput(
        section_id="proc",
        heading_path=("Calibration",),
        procedure_title="Calibration",
        steps=(
            ("Warm up the sensor.", ("WARNING: Do not exceed 50 C.",)),
            ("Record the baseline.", ()),
        ),
    )
    result = chunk_document([section], document_title="Manual")
    steps = [c for c in result.children if c.chunk_type == "procedure_step"]
    assert len(steps) == 2
    assert steps[0].text.startswith("Calibration:")
    assert "WARNING: Do not exceed 50 C." in steps[0].text
    assert "WARNING" not in steps[1].text
