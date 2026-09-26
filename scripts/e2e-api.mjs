#!/usr/bin/env node
/**
 * @file e2e-api.mjs
 * @description Ephemeral Starter API for Playwright (no SPA mount)
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-17
 * @version 0.1.1
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { spawn } from "node:child_process";
import crypto from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const dataDir = fs.mkdtempSync(path.join(os.tmpdir(), "sb-e2e-"));
const host = "127.0.0.1";
const port = process.env.E2E_API_PORT || "18080";

const env = {
  ...process.env,
  SB_TIER: "starter",
  ENVIRONMENT: "test",
  BIND_HOST: host,
  PUBLIC_URL: `http://${host}:${port}`,
  REGISTRATION_MODE: "open",
  JWT_SECRET: process.env.JWT_SECRET || crypto.randomBytes(32).toString("hex"),
  MASTER_KEY: process.env.MASTER_KEY || crypto.randomBytes(32).toString("hex"),
  SB_DATA_DIR: dataDir,
  // The e2e suite runs many sequential logins from the same IP (127.0.0.1) with no
  // delay between specs; the production default (10/min, see config.py) is correct
  // for real traffic but is exactly the kind of budget a serial test run burns through
  // by accident. Give this ephemeral test server headroom instead of tuning the real
  // limiter down for everyone.
  AUTH_RATE_LIMIT_PER_MIN: process.env.AUTH_RATE_LIMIT_PER_MIN || "1000",
};

const child = spawn(
  "uv",
  [
    "run",
    "uvicorn",
    "seismobrain_api.app:create_e2e_app",
    "--factory",
    "--host",
    host,
    "--port",
    String(port),
  ],
  { cwd: root, env, stdio: "inherit" },
);

child.on("exit", (code) => process.exit(code ?? 1));
