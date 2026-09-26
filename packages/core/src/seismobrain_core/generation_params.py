"""
File: generation_params.py
Description: Temperature 0, fixed seed, per-mode output token limits (FR-GEN-09)
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

from seismobrain_core.grounding_balanced import GroundingMode

DEFAULT_SEED = 42
DEFAULT_TEMPERATURE = 0.0

_MAX_OUTPUT_TOKENS: dict[GroundingMode, int] = {
    GroundingMode.BALANCED: 1024,
    GroundingMode.STRICT: 768,
}


@dataclass(frozen=True, slots=True)
class GenerationParams:
    temperature: float
    seed: int
    max_output_tokens: int
    mode: GroundingMode


def generation_params_for_mode(mode: GroundingMode) -> GenerationParams:
    return GenerationParams(
        temperature=DEFAULT_TEMPERATURE,
        seed=DEFAULT_SEED,
        max_output_tokens=_MAX_OUTPUT_TOKENS[mode],
        mode=mode,
    )
