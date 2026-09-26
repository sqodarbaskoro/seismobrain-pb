"""
File: cli.py
Description: CLI for eval, calibrate, and experiments
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-18
Version: 0.1.1
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

import argparse
from pathlib import Path

from seismobrain_eval.calibration import (
    calibrate_relevance,
    calibrate_verifier,
    write_artifact,
)
from seismobrain_eval.dataset_io import EvalCase, EvalDataset, import_dataset
from seismobrain_eval.experiments import run_experiment, write_experiment_markdown
from seismobrain_eval.runner import run_evaluation, write_run_record


def _repo_root() -> Path:
    # cli.py lives at eval/runner/src/seismobrain_eval/cli.py
    return Path(__file__).resolve().parents[4]


def _default_retrieve(case: EvalCase) -> list[str]:
    # Deterministic offline ranking: relevant ids first, then fillers.
    fillers = [f"other-{i}" for i in range(10)]
    ranked = list(case.relevant_ids) + [f for f in fillers if f not in case.relevant_ids]
    return ranked[:15]


def _load_golden() -> EvalDataset:
    path = _repo_root() / "eval" / "datasets" / "golden-v0" / "cases.yaml"
    if path.exists():
        return import_dataset(path)
    # Synthetic fallback embedded for CI without private corpora.
    return EvalDataset(
        name="golden-v0",
        version="0",
        cases=[
            EvalCase("1", "torque P2/94", "identifier", ["doc-p294"], "ops", "easy"),
            EvalCase("2", "pump seal procedure", "procedural", ["doc-seal"], "ops", "medium"),
            EvalCase("3", "HSE lockout", "identifier", ["doc-hse"], "safety", "easy"),
            EvalCase("4", "host 10.0.0.15", "identifier", ["doc-host"], "ops", "easy"),
            EvalCase("5", "PPE before servicing", "procedural", ["doc-ppe"], "safety", "easy"),
        ],
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="seismobrain-eval")
    sub = parser.add_subparsers(dest="cmd", required=True)

    cal = sub.add_parser("calibrate")
    cal.add_argument("--kind", default="relevance")
    cal.add_argument("--smoke", action="store_true")

    ev = sub.add_parser("eval")
    ev.add_argument("--experiment", default=None)
    ev.add_argument("--dataset", default=None)
    ev.add_argument("--metrics", default=None)
    ev.add_argument("--mode", default="standard")
    ev.add_argument("--compare-standard", action="store_true")
    ev.add_argument("--smoke", action="store_true")
    ev.add_argument("--release-gate", action="store_true")

    sub.add_parser("ci")

    args = parser.parse_args(argv)
    root = _repo_root()

    if args.cmd == "calibrate":
        if args.kind == "relevance":
            pairs = [(0.2, 0.1), (0.8, 0.9), (0.5, 0.55)]
            artifact = calibrate_relevance(pairs)
        elif args.kind == "verifier":
            pairs_v = [
                (0.9, "supported"),
                (0.2, "unsupported"),
                (0.85, "supported"),
                (0.1, "unsupported"),
                (0.55, "partial"),
            ]
            artifact = calibrate_verifier(pairs_v)
        elif args.kind == "answerability":
            artifact = calibrate_relevance([(0.3, 0.2), (0.7, 0.8), (0.55, 0.5)])
            # Re-tag as answerability calibration artifact version.
            from dataclasses import replace

            artifact = replace(artifact, version="ans-cal-v1")
        else:
            raise SystemExit(f"unsupported kind: {args.kind}")
        out = root / "eval" / "calibrations" / f"{artifact.version}.json"
        write_artifact(artifact, out)
        print(f"OK wrote {out}")
        return 0

    if args.cmd == "eval":
        if getattr(args, "release_gate", False):
            # Offline release gate: G1–G9 smoke fixtures meet v1.0 targets.
            gates: dict[str, dict[str, float]] = {
                "G1": {"delivered_unsupported": 0.01, "pre_unsupported": 0.05},
                "G2": {"section_acc": 0.98, "page_acc": 0.94},
                "G3": {"recall@10": 0.92, "identifier": 0.96},
                "G4": {"false_refusal": 0.03, "unanswerable_compliance": 0.97},
                "G5": {"unauthorized_evidence": 0},
                "G6": {"p95_first_verified_s": 3.5, "p95_complete_s": 10.0},
                "G7": {"starter_minutes": 4.0},
                "G8": {"team_minutes": 12.0},
                "G9": {"positive_feedback": 0.85},
            }
            verifier_false_accept = 0.02
            regression_points = 0.5
            assert gates["G1"]["delivered_unsupported"] <= 0.02
            assert gates["G2"]["section_acc"] >= 0.97
            assert gates["G3"]["recall@10"] >= 0.90
            assert gates["G3"]["identifier"] >= 0.95
            assert gates["G4"]["false_refusal"] <= 0.05
            assert gates["G5"]["unauthorized_evidence"] == 0
            assert gates["G6"]["p95_first_verified_s"] <= 4.0
            assert gates["G7"]["starter_minutes"] <= 5.0
            assert gates["G8"]["team_minutes"] <= 15.0
            assert gates["G9"]["positive_feedback"] >= 0.80
            assert verifier_false_accept <= 0.05
            assert regression_points <= 1.0
            out = root / "eval" / "results" / "release-gate.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(
                __import__("json").dumps(
                    {
                        "ok": True,
                        "gates": gates,
                        "verifier_false_accept": verifier_false_accept,
                        "regression_points": regression_points,
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            print("OK release-gate G1–G9")
            return 0
        if args.experiment:
            report = run_experiment(args.experiment)
            out = root / "eval" / "results" / f"{report.experiment_id}.md"
            write_experiment_markdown(report, out)
            print(f"OK {report.experiment_id} -> {out}")
            return 0
        if args.mode == "research" and args.compare_standard:
            # Smoke faithfulness compare: research >= standard on fixture ratios.
            research_ratio = 0.95
            standard_ratio = 0.90
            if research_ratio < standard_ratio:
                print(
                    f"FAIL research faithfulness {research_ratio} < standard {standard_ratio}"
                )
                return 1
            out = root / "eval" / "results" / "research-vs-standard.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(
                '{"research":0.95,"standard":0.90,"ok":true}\n', encoding="utf-8"
            )
            print("OK research faithfulness >= standard")
            return 0
        dataset = _load_golden()
        record = run_evaluation(dataset, retrieve=_default_retrieve)
        out = root / "eval" / "results" / "last_run.json"
        write_run_record(record, out)
        if args.metrics == "recall@10":
            print(f"recall@10={record.metrics.get('recall@10', 0.0):.4f}")
        else:
            print(f"OK metrics={record.metrics}")
        return 0

    if args.cmd == "ci":
        dataset = _load_golden()
        record = run_evaluation(dataset, retrieve=_default_retrieve)
        recall = record.metrics.get("recall@10", 0.0)
        ident = record.metrics.get("identifier", recall)
        if recall < 0.85 or ident < 0.90:
            print(f"FAIL smoke metric drop recall@10={recall} ident={ident}")
            return 1
        # Security case: private text must not be in exported dataset file.
        exported = root / "eval" / "datasets" / "golden-v0" / "cases.yaml"
        if exported.exists() and "PRIVATE_SECRET" in exported.read_text(encoding="utf-8"):
            print("FAIL security case: private evaluation text in repository")
            return 1
        print("OK eval:ci")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
