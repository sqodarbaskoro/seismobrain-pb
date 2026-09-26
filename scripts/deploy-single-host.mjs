/**
 * @file deploy-single-host.mjs
 * @description Hardened single-host Compose deploy (T6.2)
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

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const dryRun = process.argv.includes("--dry-run");
const base = path.join(root, "deploy/compose.yaml");
const prod = path.join(root, "deploy/compose.production.yaml");

for (const p of [base, prod]) {
  if (!fs.existsSync(p)) {
    console.error(`FAIL missing ${p}`);
    process.exit(1);
  }
}

const text = fs.readFileSync(prod, "utf8");
const checks = [
  [/TLS_MODE:\s*terminate/, "TLS"],
  [/resources:/, "resource limits"],
  [/BACKUP_CRON:/, "backups"],
  [/MONITORING:\s*enabled/, "monitoring"],
  [/NOT high availability|not HA/i, "not-HA documentation"],
];
for (const [re, label] of checks) {
  if (!re.test(text)) {
    console.error(`FAIL compose.production missing ${label}`);
    process.exit(1);
  }
}

if (dryRun) {
  console.log("OK deploy:single-host --dry-run (TLS, limits, backups, monitoring)");
  console.log("NOTE: production-hardened single-host profile is not HA");
  process.exit(0);
}

console.error("live apply requires Docker; use --dry-run for validation");
process.exit(1);
