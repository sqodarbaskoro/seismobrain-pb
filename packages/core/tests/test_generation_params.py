"""
File: test_generation_params.py
Description: Temperature 0, seed, per-mode token limits (T3.9)
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

from seismobrain_core.generation_params import generation_params_for_mode
from seismobrain_core.grounding_balanced import GroundingMode


def test_generation_params_temperature_seed_and_limits() -> None:
    balanced = generation_params_for_mode(GroundingMode.BALANCED)
    strict = generation_params_for_mode(GroundingMode.STRICT)
    assert balanced.temperature == 0.0
    assert balanced.seed == 42
    assert balanced.max_output_tokens > 0
    assert strict.max_output_tokens <= balanced.max_output_tokens
