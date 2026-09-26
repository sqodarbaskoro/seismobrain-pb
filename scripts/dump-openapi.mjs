#!/usr/bin/env node
/**
 * @file dump-openapi.mjs
 * @description Export FastAPI OpenAPI schema to openapi/openapi.json
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-17
 * @version 0.1.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const out = path.join(root, "openapi", "openapi.json");

const py = `
import json, os
os.environ.setdefault("JWT_SECRET", "a" * 64)
os.environ.setdefault("MASTER_KEY", "b" * 64)
os.environ.setdefault("SB_TIER", "starter")
os.environ.setdefault("ENVIRONMENT", "development")
from pathlib import Path
from seismobrain_adapters.authz.deny import DenyAllAuthorizationGuard
from seismobrain_adapters.event_log.in_memory import InMemoryEventLog
from seismobrain_adapters.metadata.sqlite import SqliteMetadataStore
from seismobrain_adapters.object_store.filesystem import FilesystemObjectStore
from seismobrain_adapters.queue.in_process import InProcessJobQueue
from seismobrain_adapters.rate_limit.in_memory import InMemoryRateLimiter
from seismobrain_api.app import create_app
from seismobrain_api.auth.users import InMemoryUserStore
from seismobrain_api.config import Settings
from seismobrain_api.container import AppContainer
tmp = Path("/tmp/sb-openapi-dump")
tmp.mkdir(parents=True, exist_ok=True)
app = create_app(AppContainer(
    settings=Settings(),
    metadata_store=SqliteMetadataStore(tmp / "meta.db"),
    job_queue=InProcessJobQueue(tmp / "jobs"),
    object_store=FilesystemObjectStore(tmp / "objects"),
    event_log=InMemoryEventLog(),
    rate_limiter=InMemoryRateLimiter(),
    authorization_guard=DenyAllAuthorizationGuard(),
    user_store=InMemoryUserStore(),
))
print(json.dumps(app.openapi(), indent=2))
`;

const result = spawnSync("uv", ["run", "python", "-c", py], {
  cwd: root,
  encoding: "utf8",
  env: process.env,
});
if (result.status !== 0) {
  console.error(result.stderr || result.stdout);
  process.exit(result.status ?? 1);
}
fs.mkdirSync(path.dirname(out), { recursive: true });
fs.writeFileSync(out, `${result.stdout.trim()}\n`);
console.log(`OK: wrote ${path.relative(root, out)}`);
