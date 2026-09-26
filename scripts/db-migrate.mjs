/**
 * @file db-migrate.mjs
 * @description Apply metadata schema migrations (Alembic upgrade head)
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-16
 * @modified 2026-09-16
 * @version 0.1.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { spawnSync } from "node:child_process";
import { mkdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const adapters = path.join(root, "packages/adapters");
const databaseUrl =
  process.env.DATABASE_URL ?? `sqlite+pysqlite:///${path.join(root, "data/meta.db")}`;

mkdirSync(path.join(root, "data"), { recursive: true });

const result = spawnSync(
  "uv",
  ["run", "alembic", "-c", "alembic.ini", "upgrade", "head"],
  {
    cwd: adapters,
    stdio: "inherit",
    env: { ...process.env, DATABASE_URL: databaseUrl },
  },
);

if (result.status !== 0) {
  process.exit(result.status ?? 1);
}

console.log("OK: db:migrate applied migrations to head");
