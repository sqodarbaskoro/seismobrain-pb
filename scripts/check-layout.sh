#!/usr/bin/env bash
# File: check-layout.sh
# Description: Verify SeismoBrain monorepo directories match PRD §16.1 (T0a.1)
# Author: Sri Yanto Qodarbaskoro
# Contact: sqodarbaskoro@gmail.com
# LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
# Website: https://www.seismopilot.com
# Created: 2026-09-16
# Modified: 2026-09-16
# Version: 0.1.0
# Copyright: © 2026 Sri Yanto Qodarbaskoro

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

REQUIRED=(
  apps/api
  apps/worker
  apps/models
  apps/web
  packages/core
  packages/ingest
  packages/adapters
  packages/contracts
  eval
  deploy
  config
  samples
  scripts
  docs
)

missing=0
for path in "${REQUIRED[@]}"; do
  if [[ ! -d "$path" ]]; then
    echo "MISSING: $path" >&2
    missing=1
  fi
done

if [[ "$missing" -ne 0 ]]; then
  exit 1
fi

echo "OK: monorepo layout matches PRD §16.1 required roots"
