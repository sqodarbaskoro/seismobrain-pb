"""
File: oidc_routes.py
Description: OIDC login routes (FR-AUTH-06)
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

from typing import cast

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from seismobrain_api.container import AppContainer

router = APIRouter(prefix="/api/v1/auth/oidc", tags=["oidc"])


def _container(request: Request) -> AppContainer:
    return cast(AppContainer, request.app.state.container)


class OidcLoginBody(BaseModel):
    id_token: str


@router.post("/login")
def oidc_login(body: OidcLoginBody, request: Request) -> dict[str, object]:
    try:
        return _container(request).oidc.authenticate(body.id_token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.get("/local-login")
def local_login_status(request: Request) -> dict[str, bool]:
    return {"allowed": _container(request).oidc.local_login_allowed()}
