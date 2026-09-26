"""
File: dataset_io.py
Description: Golden dataset YAML/JSONL import/export (FR-EVAL-01)
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

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]


@dataclass
class EvalCase:
    id: str
    query: str
    query_type: str
    relevant_ids: list[str]
    collection: str = "default"
    difficulty: str = "easy"
    # Private evaluation text must not be exported to the repo by default.
    private_text: str | None = None


@dataclass
class EvalDataset:
    name: str
    version: str
    cases: list[EvalCase] = field(default_factory=list)


def export_dataset(
    dataset: EvalDataset,
    path: Path,
    *,
    include_private: bool = False,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "name": dataset.name,
        "version": dataset.version,
        "cases": [],
    }
    for case in dataset.cases:
        row = asdict(case)
        if not include_private:
            row.pop("private_text", None)
        payload["cases"].append(row)
    if path.suffix in {".yaml", ".yml"}:
        path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    else:
        with path.open("w", encoding="utf-8") as handle:
            for case in payload["cases"]:
                handle.write(json.dumps(case) + "\n")


def import_dataset(path: Path) -> EvalDataset:
    text = path.read_text(encoding="utf-8")
    if path.suffix in {".yaml", ".yml"}:
        data = yaml.safe_load(text)
        cases = [EvalCase(**row) for row in data.get("cases", [])]
        return EvalDataset(
            name=data.get("name", path.stem),
            version=str(data.get("version", "0")),
            cases=cases,
        )
    cases = []
    for line in text.splitlines():
        if not line.strip():
            continue
        cases.append(EvalCase(**json.loads(line)))
    return EvalDataset(name=path.stem, version="0", cases=cases)
