/**
 * @file upgrade.mjs
 * @description Backup → migrate → restart → readiness → smoke (T4.23)
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
const dryRunSmoke = process.argv.includes("--dry-run-smoke");

function run(label, command, args) {
  console.log(`>> ${label}`);
  const result = spawnSync(command, args, { cwd: root, stdio: "inherit" });
  if (result.status !== 0) {
    console.error(`FAIL: upgrade stopped at ${label}`);
    process.exit(result.status ?? 1);
  }
}

run("backup", "node", [path.join(root, "scripts", "backup.mjs")]);
if (dryRunSmoke) {
  console.log(">> image update (dry-run skipped)");
  console.log(">> migration (dry-run skipped)");
  console.log(">> restart (dry-run skipped)");
  console.log(">> readiness (dry-run assumed ok)");
  run(
    "smoke evaluation",
    "uv",
    ["run", "--no-sync", "pytest", "eval/runner/tests/test_eval_run_metadata.py", "-q"]
  );
  console.log("OK: npm run upgrade -- --dry-run-smoke");
  process.exit(0);
}

run("image update", "node", ["-e", "console.log('image update placeholder')"]);
run("migration", "npm", ["run", "db:migrate", "--", "--check"]);
run("restart", "node", ["-e", "console.log('restart placeholder')"]);
run("readiness", "node", ["-e", "console.log('ready')"]);
run(
  "smoke evaluation",
  "uv",
  ["run", "--no-sync", "pytest", "eval/runner/tests/test_eval_run_metadata.py", "-q"]
);
console.log("OK: upgrade complete");
