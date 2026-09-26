/**
 * @file eval-env.mjs
 * @description Ensure seismobrain_eval is importable for npm eval/calibrate scripts
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
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const srcPaths = [
  path.join(root, "eval", "runner", "src"),
  path.join(root, "packages", "core", "src"),
];
const env = {
  ...process.env,
  PYTHONPATH: [...srcPaths, process.env.PYTHONPATH].filter(Boolean).join(path.delimiter),
};

const args = process.argv.slice(2);
if (args.length === 0) {
  console.error("usage: node scripts/eval-env.mjs <calibrate|eval|ci> [...args]");
  process.exit(1);
}

const result = spawnSync(
  "uv",
  ["run", "--no-sync", "python", "-m", "seismobrain_eval", ...args],
  { cwd: root, stdio: "inherit", env },
);
process.exit(result.status ?? 1);
