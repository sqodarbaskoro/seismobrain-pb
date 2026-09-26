/**
 * @file setup.mjs
 * @description Prerequisite check, .env secrets, deps install, first admin (T0c.5)
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
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const args = new Set(process.argv.slice(2));
const ciSmoke = args.has("--ci-smoke");

function run(command, commandArgs, options = {}) {
  let executable = command;
  let args = commandArgs;
  let shell = false;
  if (command === "npm") {
    if (process.env.npm_execpath) {
      executable = process.execPath;
      args = [process.env.npm_execpath, ...commandArgs];
    } else if (process.platform === "win32") {
      executable = "npm.cmd";
      shell = true;
    }
  }
  const result = spawnSync(executable, args, {
    cwd: root,
    stdio: "inherit",
    env: process.env,
    shell,
    ...options,
  });
  if (result.status !== 0) {
    if (result.error) console.error(`FAIL: ${result.error.message}`);
    process.exit(result.status ?? 1);
  }
}

function requireCmd(name) {
  const result = spawnSync(name, ["--version"], { encoding: "utf8" });
  if (result.status !== 0) {
    console.error(`FAIL: ${name} is required`);
    process.exit(1);
  }
}

function ensureEnv() {
  const envPath = path.join(root, ".env");
  if (fs.existsSync(envPath) && !ciSmoke) {
    console.log("OK: .env already present");
    return;
  }
  if (fs.existsSync(envPath) && ciSmoke) {
    console.log("OK: .env already present (ci-smoke)");
    return;
  }
  const jwt = crypto.randomBytes(32).toString("hex");
  const master = crypto.randomBytes(32).toString("hex");
  const body = [
    "SB_TIER=starter",
    "ENVIRONMENT=development",
    "BIND_HOST=127.0.0.1",
    "PUBLIC_URL=http://127.0.0.1:8080",
    "REGISTRATION_MODE=approval",
    `JWT_SECRET=${jwt}`,
    `MASTER_KEY=${master}`,
    "",
  ].join("\n");
  fs.writeFileSync(envPath, body, { encoding: "utf8", mode: 0o600 });
  console.log("OK: generated .env with random secrets");
}

function ensureFirstAdmin() {
  const adminPath = path.join(root, "data", "first-admin.json");
  fs.mkdirSync(path.dirname(adminPath), { recursive: true });
  if (!fs.existsSync(adminPath)) {
    const record = {
      email: "admin@localhost",
      name: "Administrator",
      system_role: "system_admin",
      created_by: "npm run setup",
    };
    fs.writeFileSync(adminPath, `${JSON.stringify(record, null, 2)}\n`);
  }
  console.log("OK: first admin record ready");
}

const major = Number(process.versions.node.split(".")[0]);
if (major < 22) {
  console.error(`FAIL: Node.js >= 22 required (found ${process.versions.node})`);
  process.exit(1);
}
console.log(`OK: Node.js ${process.versions.node}`);
requireCmd("uv");
console.log("OK: uv present");

ensureEnv();
if (!ciSmoke) {
  run("uv", ["sync"]);
  run("npm", ["install"]);
} else {
  // CI smoke assumes workspace deps are already installed; refresh lock if needed.
  run("uv", ["sync", "--frozen"]);
}
ensureFirstAdmin();
console.log(ciSmoke ? "OK: setup --ci-smoke complete" : "OK: setup complete");
