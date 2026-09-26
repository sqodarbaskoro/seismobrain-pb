/**
 * @file check-spa-bundle-size.mjs
 * @description Enforce SPA initial load ≤500KB gzipped (NFR-PERF-09)
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-16
 * @modified 2026-09-16
 * @version 0.1.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { createGzip } from "node:zlib";
import { createReadStream, readdirSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { pipeline } from "node:stream/promises";
import { Writable } from "node:stream";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const dist = path.join(root, "apps/web/dist");
const budget = 500 * 1024;

function collectAssets(dir) {
  const out = [];
  for (const name of readdirSync(dir)) {
    const full = path.join(dir, name);
    if (statSync(full).isDirectory()) out.push(...collectAssets(full));
    else if (/\.(js|css|html|svg|woff2?)$/i.test(name)) out.push(full);
  }
  return out;
}

async function gzipSize(file) {
  let size = 0;
  const counter = new Writable({
    write(chunk, _enc, cb) {
      size += chunk.length;
      cb();
    },
  });
  await pipeline(createReadStream(file), createGzip(), counter);
  return size;
}

const assets = collectAssets(dist);
let total = 0;
for (const file of assets) {
  total += await gzipSize(file);
}
if (total > budget) {
  console.error(`FAIL SPA gzipped=${total} budget=${budget}`);
  process.exit(1);
}
console.log(`OK SPA gzipped=${total} <= ${budget}`);
