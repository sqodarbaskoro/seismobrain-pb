/**
 * @file vite.config.ts
 * @description Vite + Vitest configuration for apps/web
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-16
 * @modified 2026-09-17
 * @version 0.1.3
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

const apiTarget = process.env.VITE_API_PROXY ?? "http://127.0.0.1:8080";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    proxy: {
      "/auth": apiTarget,
      "/api": apiTarget,
      "/admin": apiTarget,
      "/health": apiTarget,
      "/ready": apiTarget,
      // Bare (non-/api/v1) backend routes used by document preview/download and the
      // chat citation viewer — see apps/api/src/seismobrain_api/spa.py _API_ROOTS for
      // the full reserved list this needs to stay in sync with as more of it is used.
      "/documents": apiTarget,
      "/citations": apiTarget,
      "/evidence-snapshots": apiTarget,
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    exclude: ["**/node_modules/**", "**/e2e/**", "**/dist/**"],
  },
});
