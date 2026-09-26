"""
File: admin_providers.py
Description: Provider configuration routes with encrypted secrets (FR-ADM-04)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-18
Version: 0.3.1
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

from typing import Literal, cast

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import AnyHttpUrl, BaseModel, Field

from seismobrain_api.admin_catalog import ProviderRecord
from seismobrain_api.auth.deps import require_admin
from seismobrain_api.container import AppContainer
from seismobrain_api.provider_test import probe_provider
from seismobrain_core.envelope import EnvelopeCipher

router = APIRouter(prefix="/admin/providers", tags=["admin-providers"])

ProviderKind = Literal[
    "openai_compatible", "anthropic", "gemini", "ollama_vllm"
]
Locality = Literal["local", "external"]


def _container(request: Request) -> AppContainer:
    return cast(AppContainer, request.app.state.container)


class ProviderBody(BaseModel):
    kind: ProviderKind
    name: str = Field(min_length=1)
    base_url: AnyHttpUrl
    models: list[str] = Field(min_length=1)
    api_key: str = Field(min_length=1)
    locality: Locality = "external"


class ProviderUpdateBody(BaseModel):
    kind: ProviderKind
    name: str = Field(min_length=1)
    base_url: AnyHttpUrl
    models: list[str] = Field(min_length=1)
    locality: Locality = "external"
    api_key: str | None = None


def _public_provider(record: ProviderRecord) -> dict[str, object]:
    return {
        "id": record.id,
        "kind": record.kind,
        "name": record.name,
        "models": record.models,
        "base_url": record.base_url,
        "locality": record.locality,
        "secret_key_id": record.secret.key_id,
        "has_secret": True,
    }


@router.get("")
def list_providers(request: Request) -> dict[str, object]:
    require_admin(request)
    items = [_public_provider(p) for p in _container(request).admin_catalog.list_providers()]
    return {"providers": items}


@router.post("", status_code=201)
def create_provider(body: ProviderBody, request: Request) -> dict[str, object]:
    require_admin(request)
    container = _container(request)
    record = container.admin_catalog.create_provider(
        kind=body.kind,
        name=body.name,
        models=body.models,
        api_key=body.api_key,
        master_key=container.settings.master_key,
        actor="system_admin",
        base_url=str(body.base_url).rstrip("/"),
        locality=body.locality,
    )
    return _public_provider(record)


@router.put("/{provider_id}")
def update_provider(
    provider_id: str, body: ProviderUpdateBody, request: Request
) -> dict[str, object]:
    require_admin(request)
    container = _container(request)
    api_key = body.api_key.strip() if body.api_key else None
    record = container.admin_catalog.update_provider(
        provider_id,
        kind=body.kind,
        name=body.name,
        models=body.models,
        master_key=container.settings.master_key,
        actor="system_admin",
        base_url=str(body.base_url).rstrip("/"),
        locality=body.locality,
        api_key=api_key or None,
    )
    if record is None:
        raise HTTPException(status_code=404, detail="not found")
    return _public_provider(record)


@router.delete("/{provider_id}", status_code=204)
def delete_provider(provider_id: str, request: Request) -> Response:
    require_admin(request)
    deleted = _container(request).admin_catalog.delete_provider(
        provider_id, actor="system_admin"
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="not found")
    return Response(status_code=204)


@router.post("/{provider_id}/test")
def test_provider(provider_id: str, request: Request) -> dict[str, object]:
    require_admin(request)
    container = _container(request)
    record = container.admin_catalog.get_provider(provider_id)
    if record is None:
        raise HTTPException(status_code=404, detail="not found")
    plaintext = EnvelopeCipher(
        master_key=container.settings.master_key, key_id=record.secret.key_id
    ).decrypt(record.secret)
    return probe_provider(
        record,
        api_key=plaintext.decode(),
        transport=container.llm_transport,
    )
