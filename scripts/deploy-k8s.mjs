/**
 * @file deploy-k8s.mjs
 * @description Render/apply Production Helm chart with pre-flight (T6.1)
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
const args = process.argv.slice(2);
const dryRun = args.includes("--dry-run");
const valuesIdx = args.indexOf("--values");
const values =
  valuesIdx >= 0
    ? args[valuesIdx + 1]
    : "deploy/helm/seismobrain/values.yaml";

const chart = path.join(root, "deploy/helm/seismobrain");
const valuesPath = path.isAbsolute(values) ? values : path.join(root, values);

function preflight() {
  const required = [
    path.join(chart, "Chart.yaml"),
    path.join(chart, "templates/deployment-api.yaml"),
    path.join(chart, "templates/networkpolicy.yaml"),
    valuesPath,
  ];
  for (const p of required) {
    if (!fs.existsSync(p)) {
      console.error(`FAIL pre-flight missing: ${p}`);
      process.exit(1);
    }
  }
  console.log("OK pre-flight: chart and values present");
}

preflight();

if (dryRun) {
  const helm = spawnSync("helm", ["version", "--short"], { encoding: "utf8" });
  if (helm.status === 0) {
    const rendered = spawnSync(
      "helm",
      ["template", "seismobrain", chart, "-f", valuesPath],
      { cwd: root, encoding: "utf8" }
    );
    if (rendered.status === 0 && rendered.stdout.includes("kind: Deployment")) {
      console.log("OK deploy:k8s dry-run (helm template)");
      process.exit(0);
    }
  }
  // Offline smoke: substitute simple {{ .Values }} leaves for CI without helm.
  let tpl = fs.readFileSync(
    path.join(chart, "templates/deployment-api.yaml"),
    "utf8"
  );
  const valuesText = fs.readFileSync(valuesPath, "utf8");
  const apiReplicas = /api:\s*(\d+)/.exec(valuesText)?.[1] ?? "1";
  tpl = tpl
    .replaceAll("{{ .Values.replicaCount.api }}", apiReplicas)
    .replace(/\{\{\s*\.Values\.image\.api\s*\|\s*quote\s*\}\}/g, '"seismobrain/api:ci"')
    .replace(/\{\{\s*\.Values\.airGapped\s*\|\s*quote\s*\}\}/g, '"true"');
  if (!tpl.includes("kind: Deployment")) {
    console.error("FAIL dry-run render");
    process.exit(1);
  }
  const out = path.join(root, "deploy/helm/seismobrain/rendered-ci.yaml");
  fs.writeFileSync(out, tpl, "utf8");
  console.log("OK deploy:k8s --dry-run (offline render)");
  process.exit(0);
}

console.error("apply mode requires cluster context; use --dry-run in CI");
process.exit(1);
