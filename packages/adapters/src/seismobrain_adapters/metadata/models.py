"""
File: models.py
Description: Shared SQLAlchemy metadata models (hierarchy Tenant→…→DocumentVersion)
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-16
Version: 0.2.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TenantRow(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    settings: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

    workspaces: Mapped[list[WorkspaceRow]] = relationship(back_populates="tenant")


class WorkspaceRow(Base):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tenants.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    grounding_mode: Mapped[str] = mapped_column(String(64), nullable=False)
    egress_policy: Mapped[str] = mapped_column(String(64), nullable=False)
    research_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    custom_fields_schema: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

    tenant: Mapped[TenantRow] = relationship(back_populates="workspaces")
    collections: Mapped[list[CollectionRow]] = relationship(back_populates="workspace")


class CollectionRow(Base):
    __tablename__ = "collections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    path_template: Mapped[str] = mapped_column(String(512), nullable=False, default="{title}")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")

    workspace: Mapped[WorkspaceRow] = relationship(back_populates="collections")
    documents: Mapped[list[DocumentRow]] = relationship(back_populates="collection")


class DocumentRow(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    collection_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("collections.id"), nullable=False, index=True
    )
    logical_key: Mapped[str] = mapped_column(String(512), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="active")
    current_version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    deleted_at: Mapped[str | None] = mapped_column(String(64), nullable=True)

    collection: Mapped[CollectionRow] = relationship(back_populates="documents")
    versions: Mapped[list[DocumentVersionRow]] = relationship(back_populates="document")

    __table_args__ = (
        UniqueConstraint("collection_id", "logical_key", name="uq_documents_logical_key"),
    )


class DocumentVersionRow(Base):
    __tablename__ = "document_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id"), nullable=False, index=True
    )
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_uri: Mapped[str] = mapped_column(String(1024), nullable=False)
    rendition_uri: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    tree_uri: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    parser_version: Mapped[str] = mapped_column(String(64), nullable=False)
    pipeline_version: Mapped[str] = mapped_column(String(64), nullable=False)
    is_latest: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    document: Mapped[DocumentRow] = relationship(back_populates="versions")

    __table_args__ = (
        UniqueConstraint("document_id", "version_no", name="uq_document_version_no"),
    )
