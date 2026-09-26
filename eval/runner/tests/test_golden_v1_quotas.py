"""
File: test_golden_v1_quotas.py
Description: Golden v1 ≥400 cases with §15.1 quotas (T6.9)
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

from collections import Counter
from pathlib import Path

from seismobrain_eval.dataset_io import import_dataset
from seismobrain_eval.generate_golden_v1 import QUOTAS, build_golden_v1, build_security_dataset

ROOT = Path(__file__).resolve().parents[2]


def test_golden_v1_size_and_quotas() -> None:
    path = ROOT / "datasets" / "golden-v1" / "cases.yaml"
    if not path.exists():
        dataset = build_golden_v1()
        from seismobrain_eval.dataset_io import export_dataset

        export_dataset(dataset, path)
    dataset = import_dataset(path)
    assert dataset.name == "golden-v1"
    assert len(dataset.cases) >= 400
    counts = Counter(c.query_type for c in dataset.cases)
    for qtype, expected in QUOTAS:
        assert counts[qtype] == expected, f"{qtype}: {counts[qtype]} != {expected}"
    total = sum(c for _, c in QUOTAS)
    assert total == 400


def test_security_dataset_at_least_50() -> None:
    path = ROOT / "security" / "cases.yaml"
    if not path.exists():
        from seismobrain_eval.dataset_io import export_dataset

        export_dataset(build_security_dataset(50), path)
    dataset = import_dataset(path)
    assert len(dataset.cases) >= 50
    assert all(c.query_type == "security" for c in dataset.cases)
