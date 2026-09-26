/**
 * @file doctor.mjs
 * @description Diagnose SeismoBrain prerequisites and monorepo layout (PRD §16.2)
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
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const args = new Set(process.argv.slice(2));
const checkLayoutOnly = args.has("--check-layout");

const REQUIRED_DIRS = [
  "apps/api",
  "apps/worker",
  "apps/models",
  "apps/web",
  "packages/core",
  "packages/ingest",
  "packages/adapters",
  "packages/contracts",
  "eval",
  "deploy",
  "config",
  "samples",
  "scripts",
  "docs",
];

function fail(message) {
  console.error(`FAIL: ${message}`);
  process.exitCode = 1;
}

function ok(message) {
  console.log(`OK: ${message}`);
}

function checkNode() {
  const major = Number(process.versions.node.split(".")[0]);
  if (major < 22) {
    fail(`Node.js >= 22 required (found ${process.versions.node})`);
    return;
  }
  ok(`Node.js ${process.versions.node}`);
}

function checkLayout() {
  const missing = REQUIRED_DIRS.filter((d) => !fs.existsSync(path.join(root, d)));
  if (missing.length) {
    fail(`missing directories: ${missing.join(", ")}`);
    return;
  }
  ok("monorepo layout (PRD §16.1)");
}

function commandExists(name) {
  const result = spawnSync(name, ["--version"], { encoding: "utf8" });
  return result.status === 0;
}

function checkUv() {
  if (!commandExists("uv")) {
    fail("uv not found on PATH (required for Python workspace)");
    return;
  }
  const result = spawnSync("uv", ["--version"], { encoding: "utf8" });
  ok(`uv ${(result.stdout || result.stderr || "").trim()}`);
}

function checkPorts() {
  // Starter default bind; report without failing if in use (diagnostic only).
  const port = Number(process.env.SB_PORT || 8080);
  ok(`configured listen port ${port} (BIND_HOST default 127.0.0.1)`);
}

function checkConfig() {
  const example = path.join(root, ".env.example");
  if (fs.existsSync(example)) {
    ok(".env.example present");
  } else {
    ok(".env.example not yet created (expected before setup)");
  }
}

checkNode();
checkLayout();

if (!checkLayoutOnly) {
  checkUv();
  checkPorts();
  checkConfig();
}

if (process.exitCode) {
  console.error("doctor: unhealthy");
  process.exit(process.exitCode);
}

console.log(checkLayoutOnly ? "doctor: layout check healthy" : "doctor: healthy");
