"""
File: test_no_core_cycle.py
Description: Ensure contracts does not import seismobrain_core (no cycles)
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

import ast
from pathlib import Path

CONTRACTS_SRC = Path(__file__).resolve().parents[1] / "src"


def test_contracts_does_not_import_core() -> None:
    violations: list[str] = []
    for path in CONTRACTS_SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                if name == "seismobrain_core" or name.startswith("seismobrain_core."):
                    violations.append(
                        f"{path.relative_to(CONTRACTS_SRC)}:{node.lineno} imports {name}"
                    )
    assert not violations, "contracts must not import core:\n" + "\n".join(violations)
