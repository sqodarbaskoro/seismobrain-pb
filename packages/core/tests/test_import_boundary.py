"""
File: test_import_boundary.py
Description: Fail if packages/core imports framework, database, or network libraries
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

# packages/core may use plain pydantic for domain models; settings loaders are forbidden.
_FORBIDDEN_SETTINGS = "pydantic" + "_settings"
FORBIDDEN_MODULES = {
    "fastapi",
    "starlette",
    "uvicorn",
    "sqlalchemy",
    "alembic",
    "httpx",
    "requests",
    "aiohttp",
    "urllib3",
    "redis",
    "dramatiq",
    "qdrant_client",
    _FORBIDDEN_SETTINGS,
    "psycopg",
    "psycopg2",
    "asyncpg",
    "boto3",
    "botocore",
    "pymongo",
    "socket",
    "http.client",
    "urllib.request",
    "urllib.error",
}

CORE_SRC = Path(__file__).resolve().parents[1] / "src"


def _root_module(name: str) -> str:
    return name.split(".", 1)[0]


def _iter_imports(path: Path) -> list[tuple[int, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.append((node.lineno, alias.name))
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.append((node.lineno, node.module))
    return found


def test_core_source_tree_exists() -> None:
    assert CORE_SRC.is_dir(), f"missing core src at {CORE_SRC}"


def test_core_has_no_forbidden_imports() -> None:
    violations: list[str] = []
    for path in CORE_SRC.rglob("*.py"):
        for lineno, module in _iter_imports(path):
            root = _root_module(module)
            # Allow stdlib except explicitly forbidden networking modules.
            if module in FORBIDDEN_MODULES or root in FORBIDDEN_MODULES:
                rel = path.relative_to(CORE_SRC)
                violations.append(f"{rel}:{lineno} imports {module}")
    assert not violations, "Forbidden imports in packages/core:\n" + "\n".join(
        violations
    )


def test_settings_loader_module_is_forbidden_even_if_unused() -> None:
    """Document the rule: settings loaders belong outside core."""
    assert _FORBIDDEN_SETTINGS in FORBIDDEN_MODULES
