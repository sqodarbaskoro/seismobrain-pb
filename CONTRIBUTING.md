# Contributing to SeismoBrain

Thanks for your interest. This guide reflects how the repository is actually set up.

## Setup

Requirements: Node ≥ 22, Python ≥ 3.12, [`uv`](https://docs.astral.sh/uv/). Docker is needed only for tests that use `testcontainers` and for the Team tier.

```bash
git clone <your-fork-url> && cd seismobrain
npm run setup          # .env with random secrets, uv sync, npm install
npm run doctor         # sanity check
```

## Running tests and checks

```bash
npm run lint           # ruff (packages, apps, eval/runner) + eslint (scripts)
npm run typecheck      # mypy --strict + tsc
npm test               # scripts/check-layout.sh + pytest (all Python testpaths)

uv run pytest apps/api/tests/test_auth_tokens.py -q            # one file
uv run pytest packages/core --cov=packages/core --cov-fail-under=80 -q   # core coverage gate (CI)

npm test --workspace @seismobrain/web    # Vitest
npm run test:e2e                         # Playwright (boots API on :18080 + Vite on :5173)
```

Before opening a PR run `npm run lint && npm run typecheck && npm test`. CI (`.github/workflows/ci.yml`) runs the same plus the core coverage gate, `npm audit` and `pip-audit`.

If you change FastAPI routes or models, regenerate the contract and commit the results:

```bash
npm run generate:api --workspace @seismobrain/web   # openapi/openapi.json + apps/web/src/api/generated/schema.ts
```

## Code style

- Python: ruff (line length 100, rules `E,F,I,B,UP`), `mypy --strict`.
- TypeScript: strict `tsc`, ESLint. Web tests use Vitest and Playwright only, never pytest under `apps/web`.
- Source files start with a header block (File/Description/Author/Contact/LinkedIn/Created/Modified/Version/Copyright). Keep it on new files and bump `Modified`/`Version` when editing. Contributors should use their own author details on files they create.

## Architecture rules (PRs violating these will be rejected)

- `packages/core` must not import frameworks, DB, or network libraries, read env vars, or use `pydantic-settings`. Config validation lives in `apps/api` or `packages/adapters`.
- Retrieval must carry a server-built ACL filter on every prefetch arm and at the query root, and fail closed if it is missing. The authorization guard re-checks candidates after fusion and before reranking.
- No LLM-authored SQL. The LLM emits evidence IDs only; the server renders provenance.
- No silent truncation of chunk text.
- No `latest` image tags under `deploy/`; pin versions/digests.
- No secrets, document text, or prompts in logs by default.
- Tier differences live in adapters only.

## Workflow

- Test first: add a failing test, then implement. Never weaken or delete a test to make it pass.
- Branches: `feature/<short-name>`, `fix/<short-name>`, `docs/<short-name>`.
- Commits: use a short, imperative title and keep each commit focused on one change.
- PRs: describe the change and why, link an issue, list the checks you ran, and note any contract (OpenAPI) changes.

## Reporting security issues

Do not open a public issue for a vulnerability. Email the maintainer address listed in the source headers, or use GitHub's private vulnerability reporting once enabled.
