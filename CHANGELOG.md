# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-09-19

Initial public release.

### Added
- Monorepo (npm workspaces + uv workspace) with a hexagonal layout: `packages/core`, `packages/adapters`, `packages/ingest`, `packages/contracts`, `apps/api`, `apps/worker`, `apps/models`, `apps/web`.
- Starter tier: single-process FastAPI app with SQLite metadata, filesystem object store, in-process persistent job queue, and the React SPA (`npm run setup`, `npm run start:starter`).
- Team (Docker Compose) and Production (Helm) deployment definitions; PostgreSQL, Redis/Dramatiq and Qdrant adapters.
- Authentication (JWT, argon2), registration modes, API tokens, workspaces, groups, collection ACLs, OIDC routes, audit log.
- Retrieval core: identifier-aware BM25 arms, weighted RRF fusion, ACL filter that fails closed, post-fusion authorization guard, reranking hook, answerability gate, diversity selection.
- Grounded generation: evidence-ID contract, sentence verification, numeric guard, balanced/strict grounding modes, typed refusals, server-rendered citations, evidence snapshots.
- Ingestion: format validation, parsers (TXT, MD, PDF, DOCX, HTML, RTF, PPTX, XLSX, ODT), sentence-boundary chunking, document versioning and activation, quarantine, bulk/folder ingestion, purge.
- Admin UI: users, providers (OpenAI-compatible, Anthropic, Gemini), ingestion monitor, glossary, analytics.
- Evaluation runner with golden sets, calibrations and recorded experiment decisions (`eval/`).
- Ops scripts: backup/restore, upgrade, reindex, tier migration, key rotation, doctor, egress self-test.
- CI: lint, typecheck, tests, core coverage gate (≥ 80%), `npm audit`, `pip-audit`.

### Known limitations
- Starter tier uses deterministic lightweight stand-ins for embeddings, reranking and claim verification, and lightweight parsers (no OCR/layout analysis).
- Qdrant adapters are implemented but not wired into the Starter API.
- Team-tier Docker images must be built locally (`npm run docker:build`).

[Unreleased]: https://github.com/OWNER/REPO/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/OWNER/REPO/releases/tag/v0.1.0
