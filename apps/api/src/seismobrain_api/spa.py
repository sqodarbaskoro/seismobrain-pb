"""
File: spa.py
Description: Mount built React SPA static assets for Starter single-process serve
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-17
Modified: 2026-09-17
Version: 0.1.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Top-level path segments that belong to the API, not the SPA.
_API_ROOTS = frozenset(
    {
        "api",
        "auth",
        "admin",
        "health",
        "ready",
        "metrics",
        "docs",
        "redoc",
        "openapi.json",
        "documents",
        "citations",
        "evidence-snapshots",
        "conversations",
        "messages",
        "jobs",
        "evidence",
        "uploads",
    }
)


def default_spa_dist() -> Path:
    """Resolve apps/web/dist from this package or the process cwd."""
    repo_dist = Path(__file__).resolve().parents[4] / "apps" / "web" / "dist"
    if repo_dist.is_dir():
        return repo_dist
    return Path("apps/web/dist")


def _is_api_path(full_path: str) -> bool:
    root = full_path.split("/", 1)[0] if full_path else ""
    return root in _API_ROOTS


def mount_spa(app: FastAPI, dist: Path) -> None:
    """Serve index.html and /assets from a Vite build directory."""
    if not dist.is_dir() or not (dist / "index.html").is_file():
        raise FileNotFoundError(
            f"SPA dist missing at {dist}; run `npm run build` then restart"
        )

    assets = dist / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="spa-assets")

    index = dist / "index.html"

    @app.get("/", include_in_schema=False)
    async def spa_index() -> FileResponse:
        return FileResponse(index)

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str) -> FileResponse:
        if _is_api_path(full_path):
            raise HTTPException(status_code=404, detail="Not Found")
        candidate = dist / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index)
