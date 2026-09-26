/**
 * @file quarantine.ts
 * @description Typed calls for the files-needing-review (quarantine) inbox
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-17
 * @version 0.1.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { apiJson } from "@/api/client";

export type QuarantineItem = {
  id: string;
  filename: string;
  reason: string;
  status: string;
  created_at: number;
};

export function listQuarantine(): Promise<{ items: QuarantineItem[] }> {
  return apiJson("/api/v1/quarantine");
}

export function releaseQuarantineItem(itemId: string): Promise<{ id: string; status: string }> {
  return apiJson(`/api/v1/quarantine/${itemId}/release`, { method: "POST" });
}
