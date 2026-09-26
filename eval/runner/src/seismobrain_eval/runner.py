"""
File: runner.py
Description: Evaluation runner on production pipeline path (FR-EVAL-02/04)
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

import hashlib
import json
import time
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from seismobrain_eval.dataset_io import EvalCase, EvalDataset
from seismobrain_eval.metrics import RankedCase, aggregate_recall_at_k, recall_at_k

RetrieveFn = Callable[[EvalCase], list[str]]


@dataclass
class EvalRunRecord:
    code_version: str
    index_version: str
    model_ids: dict[str, str]
    config_hash: str
    dataset_version: str
    metrics: dict[str, float] = field(default_factory=dict)
    used_production_path: bool = True
    service_principal: str = "eval-runner"


def config_hash(config: dict[str, Any]) -> str:
    blob = json.dumps(config, sort_keys=True).encode()
    return hashlib.sha256(blob).hexdigest()[:16]


def run_evaluation(
    dataset: EvalDataset,
    *,
    retrieve: RetrieveFn,
    code_version: str = "0.0.0",
    index_version: str = "seismobrain_chunks_v1",
    model_ids: dict[str, str] | None = None,
    config: dict[str, Any] | None = None,
    service_principal: str = "eval-runner",
    entitlements: Sequence[str] = ("eval:read",),
) -> EvalRunRecord:
    """Execute retrieval eval under an explicit service principal."""
    if "eval:read" not in entitlements:
        raise PermissionError("eval runner requires eval:read entitlement")
    models = model_ids or {"embed": "cpu-hash", "rerank": "cpu-rerank"}
    cfg = config or {"pipeline": "production"}
    ranked_cases: list[RankedCase] = []
    for case in dataset.cases:
        ranked = retrieve(case)
        ranked_cases.append(
            RankedCase(
                case_id=case.id,
                query_type=case.query_type,
                collection=case.collection,
                difficulty=case.difficulty,
                ranked_ids=ranked,
                relevant_ids=case.relevant_ids,
            )
        )
    metrics = aggregate_recall_at_k(ranked_cases, k=10)
    metrics["recall@10"] = metrics.get("all", 0.0)
    return EvalRunRecord(
        code_version=code_version,
        index_version=index_version,
        model_ids=models,
        config_hash=config_hash(cfg),
        dataset_version=dataset.version,
        metrics=metrics,
        used_production_path=cfg.get("pipeline") == "production",
        service_principal=service_principal,
    )


def write_run_record(record: EvalRunRecord, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(record), indent=2) + "\n", encoding="utf-8")


def measure_retrieval_latency_ms(
    retrieve: Callable[[], list[str]], *, iterations: int = 20
) -> float:
    samples: list[float] = []
    for _ in range(iterations):
        started = time.perf_counter()
        retrieve()
        samples.append((time.perf_counter() - started) * 1000.0)
    samples.sort()
    idx = max(0, int(0.95 * (len(samples) - 1)))
    return samples[idx]


def case_recall(case: EvalCase, ranked: Sequence[str], *, k: int = 10) -> float:
    return recall_at_k(ranked, case.relevant_ids, k=k)
