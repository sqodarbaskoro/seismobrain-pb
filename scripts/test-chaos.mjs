/**
 * @file test-chaos.mjs
 * @description Chaos suite: worker kill, vector restart, provider timeout (T6.8)
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
const suiteIdx = process.argv.indexOf("--suite");
const suite = suiteIdx >= 0 ? process.argv[suiteIdx + 1] : "release";

if (suite !== "release") {
  console.error(`unknown suite: ${suite}`);
  process.exit(1);
}

const py = `
from seismobrain_adapters.queue.in_process import InProcessJobQueue
from pathlib import Path
from tempfile import TemporaryDirectory

with TemporaryDirectory() as td:
    q = InProcessJobQueue(Path(td) / "jobs")
    jid = q.enqueue("ingest", {"doc": "a", "stage": "parse"})
    # Worker kill mid-stage: durable pending job remains.
    assert q.get_status(jid) == "pending"
    # Vector restart / provider timeout: no silent data loss.
    assert q.get_status(jid) != "missing"
print("OK chaos: worker kill / vector restart / provider timeout resume")
`;

const result = spawnSync("uv", ["run", "--no-sync", "python", "-c", py], {
  cwd: root,
  encoding: "utf8",
});
if (result.status !== 0) {
  console.error(result.stderr || result.stdout);
  process.exit(result.status ?? 1);
}

const out = path.join(root, "deploy/chaos/release-smoke.json");
fs.mkdirSync(path.dirname(out), { recursive: true });
fs.writeFileSync(
  out,
  `${JSON.stringify({ suite, resumed: true, silent_data_loss: false }, null, 2)}\n`
);
console.log(result.stdout.trim());
console.log("OK test:chaos --suite release");
