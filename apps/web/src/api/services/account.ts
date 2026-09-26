/**
 * @file account.ts
 * @description Typed calls for self-service account security: sessions, API keys
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-19
 * @version 0.2.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { apiJson } from "@/api/client";

export type SessionRow = { id: string; created_at: number; user_agent: string; ip: string };
export type ApiTokenRow = {
  id: string;
  name: string;
  scopes: string[];
  expires_at: number;
  kind: "personal" | "service";
  revoked: boolean;
};

// The only scope the server currently accepts and enforces (FR-AUTH-07 / T04.1).
export type ApiKeyScope = "read";
export const API_KEY_SCOPES: { value: ApiKeyScope; label: string; description: string }[] = [
  {
    value: "read",
    label: "Read",
    description: "List and read your collections, documents, and conversations.",
  },
];

export function listSessions(): Promise<{ sessions: SessionRow[] }> {
  return apiJson("/api/v1/sessions");
}

export function revokeSession(id: string): Promise<{ revoked: boolean }> {
  return apiJson(`/api/v1/sessions/${id}/revoke`, { method: "POST" });
}

export function listApiTokens(): Promise<{ tokens: ApiTokenRow[] }> {
  return apiJson("/api/v1/api-tokens");
}

export function issueApiToken(input: {
  name: string;
  scopes: ApiKeyScope[];
  ttl_seconds: number;
}): Promise<{ id: string; token: string; scopes: string[]; expires_at: number }> {
  return apiJson("/api/v1/api-tokens", { method: "POST", body: JSON.stringify(input) });
}

export function deleteApiToken(id: string): Promise<{ deleted: boolean }> {
  return apiJson(`/api/v1/api-tokens/${id}`, { method: "DELETE" });
}
