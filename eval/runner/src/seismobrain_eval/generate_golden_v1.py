"""
File: generate_golden_v1.py
Description: Generate golden-v1 (≥400 cases) with §15.1 coverage quotas (T6.9)
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

from seismobrain_eval.dataset_io import EvalCase, EvalDataset, export_dataset

# §15.1 quotas for 400 cases
QUOTAS: list[tuple[str, int]] = [
    ("identifier", 80),
    ("procedural", 40),
    ("table_parameter", 60),
    ("cross_page", 40),
    ("multi_document", 40),
    ("follow_up", 40),
    ("unanswerable", 60),
    ("revision_ocr_figure", 40),
]


def build_golden_v1() -> EvalDataset:
    cases: list[EvalCase] = []
    n = 0
    for qtype, count in QUOTAS:
        for i in range(count):
            n += 1
            cases.append(
                EvalCase(
                    id=str(n),
                    query=f"{qtype} query {i+1} case-{n}",
                    query_type=qtype,
                    relevant_ids=[] if qtype == "unanswerable" else [f"doc-{qtype}-{i+1}"],
                    collection="ops" if i % 2 == 0 else "safety",
                    difficulty=["easy", "medium", "hard"][i % 3],
                )
            )
    assert len(cases) == 400
    return EvalDataset(name="golden-v1", version="1", cases=cases)


def build_security_dataset(n: int = 50) -> EvalDataset:
    cases = [
        EvalCase(
            id=f"sec-{i+1}",
            query=f"security case {i+1} cross-user or injection probe",
            query_type="security",
            relevant_ids=[f"sec-doc-{i+1}"],
            collection="security",
            difficulty="hard",
        )
        for i in range(n)
    ]
    return EvalDataset(name="security-v1", version="1", cases=cases)


def main() -> None:
    # generate_golden_v1.py → seismobrain_eval → src → runner → eval
    eval_root = Path(__file__).resolve().parents[3]
    golden = build_golden_v1()
    export_dataset(golden, eval_root / "datasets" / "golden-v1" / "cases.yaml")
    security = build_security_dataset(50)
    export_dataset(security, eval_root / "security" / "cases.yaml")
    print(f"OK wrote golden-v1={len(golden.cases)} security={len(security.cases)}")


if __name__ == "__main__":
    main()
