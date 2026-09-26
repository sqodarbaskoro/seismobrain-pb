/**
 * @file sample-load.mjs
 * @description Index bundled sample corpus (T1.40)
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
const smoke = process.argv.includes("--smoke");
const args = ["run", "python", "-m", "seismobrain_ingest.sample_load"];
if (smoke) args.push("--smoke");

const result = spawnSync("uv", args, { cwd: root, stdio: "inherit" });
process.exit(result.status ?? 1);
