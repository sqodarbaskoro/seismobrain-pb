"""
File: test_vision_descriptions.py
Description: Vision descriptions labelled AI-generated (T5.13)
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

from seismobrain_ingest.vision_descriptions import describe_figure


def test_vision_description_labelled_ai_generated() -> None:
    desc = describe_figure(
        page=3,
        figure_hint="pump diagram",
        model_text="A centrifugal pump schematic.",
    )
    assert desc.extraction_method == "vision"
    assert desc.label == "AI-generated interpretation"
    assert "pump" in desc.text.lower()
