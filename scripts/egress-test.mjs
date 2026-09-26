/**
 * @file egress-test.mjs
 * @description Verify air-gapped network denial / egress self-test (T4.16, SEC-26)
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-16
 * @modified 2026-09-16
 * @version 0.1.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const composePath = path.join(root, "deploy", "compose.yaml");
const overlayPath = path.join(root, "deploy", "compose.air-gapped.yaml");

function fail(msg) {
  console.error(`FAIL: ${msg}`);
  process.exit(1);
}

const compose = fs.readFileSync(composePath, "utf8");
if (!/internal:\s*\n\s*internal:\s*true/.test(compose)) {
  fail("deploy/compose.yaml must declare an internal: true network");
}
if (!fs.existsSync(overlayPath)) {
  fail("deploy/compose.air-gapped.yaml missing");
}
const overlay = fs.readFileSync(overlayPath, "utf8");
if (!overlay.includes("AIR_GAPPED") || !overlay.includes("internal")) {
  fail("air-gapped overlay must set AIR_GAPPED and keep internal networking");
}

const py = spawnSync(
  "uv",
  [
    "run",
    "--no-sync",
    "python",
    "-c",
    "from seismobrain_api.air_gapped import run_egress_self_test, assert_air_gapped_startup; "
    + "r=run_egress_self_test(probe=lambda: False); "
    + "assert r.passed; "
    + "assert_air_gapped_startup(air_gapped=True, self_test=r); "
    + "print('OK: egress self-test')",
  ],
  { cwd: root, encoding: "utf8" }
);
if (py.status !== 0) {
  console.error(py.stdout || "");
  console.error(py.stderr || "");
  fail("egress self-test python check failed");
}

console.log("OK: npm run egress:test — network deny config + self-test passed");
