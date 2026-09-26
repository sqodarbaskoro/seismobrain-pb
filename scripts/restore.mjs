/**
 * @file restore.mjs
 * @description Restore from a backup bundle with optional smoke eval (T4.22, T6.6)
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
const raw = process.argv.slice(2).filter((a) => a !== "--");
const smoke = raw.includes("--smoke");
const verifyDrill = raw.includes("--verify-drill");
const freshCluster = raw.includes("--fresh-cluster");

function flagValue(flag) {
  const idx = raw.indexOf(flag);
  return idx >= 0 ? raw[idx + 1] : null;
}

const tier = flagValue("--tier");
const consumed = new Set();
for (let i = 0; i < raw.length; i++) {
  if (raw[i].startsWith("--")) {
    consumed.add(i);
    if (
      ["--tier"].includes(raw[i]) &&
      i + 1 < raw.length &&
      !raw[i + 1].startsWith("--")
    ) {
      consumed.add(i + 1);
    }
  }
}
const name = raw.find((_, i) => !consumed.has(i)) ?? null;

let bundleName = name;
if (!bundleName && tier) {
  const pointer = path.join(root, "backups", `latest-${tier}.txt`);
  if (fs.existsSync(pointer)) {
    bundleName = fs.readFileSync(pointer, "utf8").trim();
  }
}

if (!bundleName) {
  console.error(
    "Usage: npm run restore -- <bundle> [--smoke|--verify-drill] | --tier production --fresh-cluster --verify-drill"
  );
  process.exit(1);
}

const bundleDir = path.isAbsolute(bundleName)
  ? bundleName
  : path.join(root, "backups", bundleName);

if (!fs.existsSync(path.join(bundleDir, "manifest.json"))) {
  console.error(`FAIL: missing manifest in ${bundleDir}`);
  process.exit(1);
}

const restoreRoot = path.join(
  root,
  "data",
  freshCluster ? "restored-fresh-cluster" : "restored"
);
fs.mkdirSync(restoreRoot, { recursive: true });
fs.copyFileSync(
  path.join(bundleDir, "manifest.json"),
  path.join(restoreRoot, "manifest.json")
);
const dataSrc = path.join(bundleDir, "data");
if (fs.existsSync(dataSrc)) {
  spawnSync("cp", ["-R", dataSrc, path.join(restoreRoot, "data")], { cwd: root });
}

for (const extra of ["qdrant-topology.json", "collection-snapshots.json"]) {
  const src = path.join(bundleDir, extra);
  if (fs.existsSync(src)) {
    fs.copyFileSync(src, path.join(restoreRoot, extra));
  }
}

const consistency = JSON.parse(
  fs.readFileSync(path.join(bundleDir, "consistency.json"), "utf8")
);
if (!consistency.metadata_ok || !consistency.vectors_ok) {
  console.error("FAIL: consistency check failed");
  process.exit(1);
}
if (tier === "production" || freshCluster) {
  if (consistency.aliases_ok === false || consistency.topology_ok === false) {
    console.error("FAIL: production topology/alias consistency failed");
    process.exit(1);
  }
  if (!fs.existsSync(path.join(bundleDir, "qdrant-topology.json"))) {
    console.error("FAIL: production restore requires qdrant-topology.json");
    process.exit(1);
  }
}

if (smoke || verifyDrill) {
  const result = spawnSync(
    "uv",
    ["run", "--no-sync", "pytest", "eval/runner/tests/test_eval_run_metadata.py", "-q"],
    { cwd: root, stdio: "inherit" }
  );
  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
  console.log(
    verifyDrill
      ? "OK: restore verify-drill passed"
      : "OK: restore smoke eval passed"
  );
}

if (freshCluster) {
  console.log("OK: restored onto fresh-cluster target");
}
console.log(`OK: restored ${path.basename(bundleDir)}`);
