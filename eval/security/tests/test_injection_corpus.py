"""
File: test_injection_corpus.py
Description: Prompt-injection corpus — all success counts must be 0 (T4.17)
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

import yaml

from seismobrain_core.injection_defense import InjectionCase, evaluate_injection_case

CORPUS = Path(__file__).resolve().parents[1] / "corpus" / "cases.yaml"


def test_injection_corpus_all_success_counts_zero() -> None:
    data = yaml.safe_load(CORPUS.read_text(encoding="utf-8"))
    cases = [
        InjectionCase(
            id=row["id"],
            category=row["category"],
            attack_text=row["attack_text"],
            question=row["question"],
        )
        for row in data["cases"]
    ]
    assert len(cases) >= 5
    successes = 0
    failures: list[str] = []
    for case in cases:
        result = evaluate_injection_case(case)
        if result.success:
            successes += 1
            failures.append(f"{case.id}:{','.join(result.reasons)}")
    assert successes == 0, failures
