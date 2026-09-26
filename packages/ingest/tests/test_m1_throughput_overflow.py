"""
File: test_m1_throughput_overflow.py
Description: FR-CHK-04 / M1 — measure ingest throughput; zero chunk overflow
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

from pathlib import Path

from seismobrain_api.metrics import CHUNK_OVERFLOW_TOTAL, render_metrics
from seismobrain_ingest.sample_load import load_sample_corpus


def test_sample_load_throughput_and_zero_overflow(tmp_path: Path) -> None:
    result = load_sample_corpus(work_dir=tmp_path / "work", smoke=False)
    assert result.files >= 1
    assert result.chunks >= 1
    assert result.embedded == result.chunks
    assert result.duration_seconds > 0
    assert result.truncations == 0
    assert "EMBEDDED" in result.stages
    metrics = render_metrics().decode("utf-8")
    assert "sb_chunk_overflow_total" in metrics
    # Counter must remain at zero (no increments during sample load).
    line = next(
        ln
        for ln in metrics.splitlines()
        if ln.startswith("sb_chunk_overflow_total")
    )
    assert line.rsplit(" ", 1)[-1] in {"0", "0.0"}


# Keep import used so metrics registry initializes with the series present.
_ = CHUNK_OVERFLOW_TOTAL
