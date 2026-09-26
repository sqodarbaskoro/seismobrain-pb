/**
 * @file docker-up.mjs
 * @description Bring up Team compose profiles with health waiting (T0c.7)
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
const smoke = process.argv.includes("--smoke");
const airGapped = process.argv.includes("--air-gapped");
const composeFile = path.join(root, "deploy", "compose.yaml");
const airGappedOverlay = path.join(root, "deploy", "compose.air-gapped.yaml");

function run(command, args) {
  const result = spawnSync(command, args, {
    cwd: root,
    stdio: "inherit",
    env: process.env,
  });
  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}

function ensurePgSecret() {
  const secretDir = path.join(root, "deploy", "secrets");
  const secretFile = path.join(secretDir, "pg_password");
  fs.mkdirSync(secretDir, { recursive: true });
  if (!fs.existsSync(secretFile)) {
    fs.writeFileSync(secretFile, `${crypto.randomBytes(24).toString("hex")}\n`, {
      mode: 0o600,
    });
    console.log("OK: wrote deploy/secrets/pg_password");
  }
}

function composeArgs(extra) {
  const plugin = spawnSync("docker", ["compose", "version"], { encoding: "utf8" });
  if (plugin.status === 0) {
    return ["docker", ["compose", ...extra]];
  }
  const standalone = spawnSync("docker-compose", ["version"], { encoding: "utf8" });
  if (standalone.status === 0) {
    return ["docker-compose", extra];
  }
  console.error("FAIL: docker compose is required");
  process.exit(1);
}

function runCompose(extra) {
  const [command, args] = composeArgs(extra);
  run(command, args);
}

ensurePgSecret();

if (airGapped) {
  run("node", [path.join(root, "scripts", "egress-test.mjs")]);
  const files = ["-f", composeFile, "-f", airGappedOverlay];
  if (smoke) {
    runCompose([...files, "--profile", "infra", "config"]);
    console.log("OK: docker:up --air-gapped --smoke config valid");
    process.exit(0);
  }
  runCompose([...files, "--profile", "core", "up", "-d", "--wait"]);
  console.log("OK: docker:up --air-gapped core profile healthy");
  process.exit(0);
}

if (smoke) {
  // Validate compose and bring infra profile to healthy (app images land with docker:build).
  runCompose(["-f", composeFile, "--profile", "infra", "config"]);
  runCompose([
    "-f",
    composeFile,
    "--profile",
    "infra",
    "up",
    "-d",
    "--wait",
  ]);
  console.log("OK: docker:up --smoke infra profile healthy");
  runCompose(["-f", composeFile, "--profile", "infra", "down"]);
  process.exit(0);
}

runCompose(["-f", composeFile, "--profile", "core", "up", "-d", "--wait"]);
console.log("OK: docker:up core profile healthy");
