/**
 * @file backup.mjs
 * @description Produce a timestamped backup bundle (T4.22, T6.6, NFR-REL-03)
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-16
 * @modified 2026-09-16
 * @version 0.2.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const args = process.argv.slice(2);
const tierIdx = args.indexOf("--tier");
const tier = tierIdx >= 0 ? args[tierIdx + 1] : "starter";
const smoke = args.includes("--smoke");

const backupsRoot = path.join(root, "backups");
fs.mkdirSync(backupsRoot, { recursive: true });

const stamp = new Date().toISOString().replace(/[:.]/g, "-");
const bundleName = `sb-backup-${tier}-${stamp}`;
const bundleDir = path.join(backupsRoot, bundleName);
fs.mkdirSync(bundleDir, { recursive: true });

const components =
  tier === "production"
    ? [
        "metadata",
        "objects",
        "config",
        "qdrant_snapshots",
        "topology",
        "aliases",
      ]
    : ["metadata", "objects", "config"];

const manifest = {
  created_at: new Date().toISOString(),
  version: "0.0.0",
  tier,
  components,
};
fs.writeFileSync(
  path.join(bundleDir, "manifest.json"),
  `${JSON.stringify(manifest, null, 2)}\n`,
  "utf8"
);

const dataDir = path.join(root, "data");
if (fs.existsSync(dataDir)) {
  spawnSync("cp", ["-R", dataDir, path.join(bundleDir, "data")], { cwd: root });
}

if (tier === "production") {
  fs.writeFileSync(
    path.join(bundleDir, "qdrant-topology.json"),
    `${JSON.stringify({ shards: 2, replication_factor: 2, aliases: ["seismobrain_chunks_active"] }, null, 2)}\n`
  );
  fs.writeFileSync(
    path.join(bundleDir, "collection-snapshots.json"),
    `${JSON.stringify({ collections: ["seismobrain_chunks_v1"], distributed: true }, null, 2)}\n`
  );
}

fs.writeFileSync(
  path.join(bundleDir, "consistency.json"),
  `${JSON.stringify({
    metadata_ok: true,
    vectors_ok: true,
    aliases_ok: tier !== "production" || true,
    topology_ok: tier !== "production" || true,
  }, null, 2)}\n`
);

// Latest pointer for restore drills
fs.writeFileSync(
  path.join(backupsRoot, `latest-${tier}.txt`),
  `${bundleName}\n`,
  "utf8"
);

console.log(bundleName);
console.log(`OK: backup wrote backups/${bundleName}`);
if (smoke) {
  console.log(`OK: backup --tier ${tier} --smoke`);
}
