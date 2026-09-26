"""
File: vision_descriptions.py
Description: Vision descriptions labelled AI-generated (FR-PARSE-05)
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

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VisionDescription:
    page: int
    text: str
    label: str
    extraction_method: str


def describe_figure(
    *,
    page: int,
    figure_hint: str,
    model_text: str,
) -> VisionDescription:
    """Optional vision model output; always labelled AI-generated interpretation."""
    _ = figure_hint
    return VisionDescription(
        page=page,
        text=model_text.strip(),
        label="AI-generated interpretation",
        extraction_method="vision",
    )
