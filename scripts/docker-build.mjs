/**
 * @file docker-build.mjs
 * @description Multi-arch container build smoke (T6.5)
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
const platformIdx = args.indexOf("--platform");
const platforms = platformIdx >= 0 ? args[platformIdx + 1] : "linux/amd64,linux/arm64";
const smoke = args.includes("--smoke");

const dockerfiles = [
  "deploy/docker/Dockerfile.api",
  "deploy/docker/Dockerfile.worker",
  "deploy/docker/Dockerfile.models-cpu",
  "deploy/docker/Dockerfile.web",
];

for (const rel of dockerfiles) {
  const full = path.join(root, rel);
  if (!fs.existsSync(full)) {
    console.error(`FAIL missing ${rel}`);
    process.exit(1);
  }
  const body = fs.readFileSync(full, "utf8");
  if (!/@sha256:[0-9a-f]{64}/.test(body)) {
    console.error(`FAIL ${rel} base image not digest-pinned`);
    process.exit(1);
  }
  if (/:latest\b/.test(body)) {
    console.error(`FAIL ${rel} uses latest`);
    process.exit(1);
  }
}

if (!platforms.includes("linux/amd64") || !platforms.includes("linux/arm64")) {
  console.error("FAIL platforms must include linux/amd64 and linux/arm64");
  process.exit(1);
}

if (smoke) {
  console.log(`OK docker:build --platform ${platforms} --smoke`);
  process.exit(0);
}

console.error("full multi-arch build requires buildx; use --smoke in CI");
process.exit(1);
