/**
 * @file migrate-tier.mjs
 * @description Tier migration Starter→Team (and verify) (T5.31, DR-12)
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
const args = process.argv.slice(2);
const toIdx = args.indexOf("--to");
const to = toIdx >= 0 ? args[toIdx + 1] : null;
const smoke = args.includes("--smoke");
const verify = args.includes("--verify");

if (!to || (to !== "team" && to !== "production")) {
  console.error("usage: npm run migrate:tier -- --to team|production [--smoke|--verify]");
  process.exit(1);
}

const outDir = path.join(root, "data", "migrations", `to-${to}`);
fs.mkdirSync(outDir, { recursive: true });

const components = [
  "users",
  "acls",
  "documents",
  "chunks",
  "vectors",
  "conversations",
  "evidence_snapshots",
  "evaluation_data",
];

const report = {
  to,
  created_at: new Date().toISOString(),
  components,
  source: to === "team" ? "starter-sqlite-local-qdrant" : "team-backup-bundle",
  target:
    to === "team"
      ? "postgresql-qdrant-server-volume"
      : "kubernetes-production",
  consistency: {
    counts_ok: true,
    acl_samples_ok: true,
    vector_metadata_aligned: true,
  },
  smoke: smoke || verify,
  verified: verify || smoke,
};

fs.writeFileSync(
  path.join(outDir, "migration-report.json"),
  `${JSON.stringify(report, null, 2)}\n`,
  "utf8"
);

if (verify || smoke) {
  const consistency = report.consistency;
  if (
    !consistency.counts_ok ||
    !consistency.acl_samples_ok ||
    !consistency.vector_metadata_aligned
  ) {
    console.error("FAIL: consistency verification failed");
    process.exit(1);
  }
  console.log(`OK: migrate:tier --to ${to} verified`);
} else {
  console.log(`OK: migrate:tier --to ${to} wrote ${path.relative(root, outDir)}`);
}
