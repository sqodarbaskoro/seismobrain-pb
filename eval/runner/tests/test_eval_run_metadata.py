"""
File: test_eval_run_metadata.py
Description: Eval run records versions and config hash (T2.23)
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

from seismobrain_eval.dataset_io import EvalCase, EvalDataset
from seismobrain_eval.runner import config_hash, run_evaluation, write_run_record


def test_run_record_includes_versions_and_config_hash(tmp_path: Path) -> None:
    dataset = EvalDataset(
        name="golden-v0",
        version="0",
        cases=[EvalCase("1", "q", "factual", ["a"])],
    )
    cfg = {"pipeline": "production", "ret_fused_pool_k": 100}
    record = run_evaluation(
        dataset,
        retrieve=lambda c: list(c.relevant_ids),
        code_version="0.1.0",
        index_version="seismobrain_chunks_v1",
        model_ids={"embed": "cpu-hash", "rerank": "cpu-rerank"},
        config=cfg,
    )
    assert record.code_version == "0.1.0"
    assert record.index_version == "seismobrain_chunks_v1"
    assert record.model_ids["embed"] == "cpu-hash"
    assert record.dataset_version == "0"
    assert record.config_hash == config_hash(cfg)
    out = tmp_path / "run.json"
    write_run_record(record, out)
    assert out.stat().st_size > 0
