"""
File: test_dataset_io.py
Description: Golden dataset import/export tests (T2.20)
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

from seismobrain_eval.dataset_io import EvalCase, EvalDataset, export_dataset, import_dataset


def test_yaml_roundtrip_strips_private_text_by_default(tmp_path: Path) -> None:
    dataset = EvalDataset(
        name="golden-v0",
        version="0",
        cases=[
            EvalCase(
                id="1",
                query="torque P2/94",
                query_type="identifier",
                relevant_ids=["doc-a"],
                private_text="PRIVATE_SECRET",
            )
        ],
    )
    path = tmp_path / "cases.yaml"
    export_dataset(dataset, path, include_private=False)
    text = path.read_text(encoding="utf-8")
    assert "PRIVATE_SECRET" not in text
    loaded = import_dataset(path)
    assert loaded.cases[0].id == "1"
    assert loaded.cases[0].private_text is None


def test_jsonl_export_include_private(tmp_path: Path) -> None:
    dataset = EvalDataset(
        name="tmp",
        version="0",
        cases=[
            EvalCase(
                id="1",
                query="q",
                query_type="factual",
                relevant_ids=["d"],
                private_text="PRIVATE_SECRET",
            )
        ],
    )
    path = tmp_path / "cases.jsonl"
    export_dataset(dataset, path, include_private=True)
    assert "PRIVATE_SECRET" in path.read_text(encoding="utf-8")
