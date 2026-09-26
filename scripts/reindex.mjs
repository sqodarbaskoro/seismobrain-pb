/**
 * @file reindex.mjs
 * @description Re-index workflow smoke: build target, evaluate, cut-over (T5.25)
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
const args = process.argv.slice(2);
const targetIdx = args.indexOf("--target");
const target = targetIdx >= 0 ? args[targetIdx + 1] : "v-test";
const smoke = args.includes("--smoke");

if (!smoke) {
  console.error("usage: npm run reindex -- --target <name> --smoke");
  process.exit(1);
}

const py = `
from pathlib import Path
from tempfile import TemporaryDirectory
from seismobrain_adapters.vector.qdrant_local import QdrantLocalVectorStore
from seismobrain_adapters.vector.reindex_cutover import ReindexWorkflow
from seismobrain_core.ports import VectorPoint

with TemporaryDirectory() as td:
    store = QdrantLocalVectorStore(Path(td) / "data")
    wf = ReindexWorkflow(vector_size=4)
    result = wf.run(
        store,
        [VectorPoint(id="33333333-3333-3333-3333-333333333333",
                     vector=[0.0, 0.0, 1.0, 0.0], payload={"mark": "smoke"})],
        target="seismobrain_chunks_${target}",
        metrics={"recall@10": 0.95},
        probe_query=[0.0, 0.0, 1.0, 0.0],
    )
    assert result.query_failures_during_switch == 0
    assert result.active.endswith("${target}")
    store.close()
print("OK reindex smoke target=${target}")
`;

const result = spawnSync(
  "uv",
  ["run", "--no-sync", "python", "-c", py],
  { cwd: root, stdio: "inherit" }
);
process.exit(result.status ?? 1);
