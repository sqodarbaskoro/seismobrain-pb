/**
 * @file start-starter.mjs
 * @description Start Starter tier on 127.0.0.1:8080 (T0c.6)
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-16
 * @modified 2026-09-17
 * @version 0.1.2
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { spawn, spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const smoke = process.argv.includes("--smoke");
const host = "127.0.0.1";
const port = 8080;
const spaIndex = path.join(root, "apps/web/dist/index.html");

function runNpm(args) {
  // npm is a .cmd shim on Windows, which child_process cannot execute directly
  // without a shell. npm_execpath points at npm-cli.js when this script is
  // launched by npm and avoids shell quoting issues on every platform.
  const npmCli = process.env.npm_execpath;
  return npmCli
    ? spawnSync(process.execPath, [npmCli, ...args], {
        cwd: root,
        stdio: "inherit",
        env: process.env,
      })
    : spawnSync(process.platform === "win32" ? "npm.cmd" : "npm", args, {
        cwd: root,
        stdio: "inherit",
        env: process.env,
        shell: process.platform === "win32",
      });
}

function ensureSpaBuilt() {
  if (fs.existsSync(spaIndex)) return;
  console.log("Building web app (apps/web/dist missing)...");
  const result = runNpm(["run", "build"]);
  if (result.status !== 0 || !fs.existsSync(spaIndex)) {
    if (result.error) console.error(`FAIL: ${result.error.message}`);
    console.error("FAIL: could not build SPA; run `npm run build`");
    process.exit(result.status ?? 1);
  }
}

function loadEnvFile() {
  const envPath = path.join(root, ".env");
  if (!fs.existsSync(envPath)) {
    console.error("FAIL: .env missing; run npm run setup first");
    process.exit(1);
  }
  const env = { ...process.env };
  for (const line of fs.readFileSync(envPath, "utf8").split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const idx = trimmed.indexOf("=");
    if (idx <= 0) continue;
    env[trimmed.slice(0, idx)] = trimmed.slice(idx + 1);
  }
  return env;
}

async function waitHealthy(timeoutMs = 20000) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    try {
      const res = await fetch(`http://${host}:${port}/health`);
      if (res.ok) return;
    } catch {
      // retry
    }
    await new Promise((r) => setTimeout(r, 200));
  }
  throw new Error("starter health check timed out");
}

ensureSpaBuilt();

const env = loadEnvFile();
env.BIND_HOST = host;

const child = spawn(
  "uv",
  [
    "run",
    "uvicorn",
    "seismobrain_api.starter:build_starter_app",
    "--factory",
    "--host",
    host,
    "--port",
    String(port),
  ],
  {
    cwd: root,
    env,
    stdio: smoke ? "ignore" : "inherit",
    detached: smoke,
  },
);

if (smoke) {
  child.unref();
  waitHealthy()
    .then(() => {
      console.log(`OK: starter smoke healthy on http://${host}:${port}`);
      process.exit(0);
    })
    .catch((err) => {
      console.error(`FAIL: ${err.message}`);
      try {
        process.kill(-child.pid, "SIGTERM");
      } catch {
        // ignore
      }
      process.exit(1);
    });
} else {
  child.on("exit", (code) => process.exit(code ?? 1));
}
