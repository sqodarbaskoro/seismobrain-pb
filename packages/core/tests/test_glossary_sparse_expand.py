"""
File: test_glossary_sparse_expand.py
Description: Workspace glossary expands sparse query only (T4.13)
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

from seismobrain_core.glossary_sparse_expand import expand_sparse_with_glossary


def test_glossary_expands_sparse_not_dense() -> None:
    result = expand_sparse_with_glossary(
        "What is the HVAC setpoint?",
        {"HVAC": "heating ventilation air conditioning"},
    )
    assert result.dense_text == "What is the HVAC setpoint?"
    assert "heating ventilation air conditioning" in result.sparse_text
    assert result.dense_text != result.sparse_text
    assert result.expansions == ("heating ventilation air conditioning",)
