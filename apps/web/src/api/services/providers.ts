/**
 * @file providers.ts
 * @description Typed admin calls for LLM provider list/update/delete/test
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

export type ProviderKind = "openai_compatible" | "anthropic" | "gemini" | "ollama_vllm";
export type ProviderLocality = "local" | "external";

export type ProviderRow = {
  id: string;
  name: string;
  kind: ProviderKind | string;
  base_url: string;
  locality: ProviderLocality | string;
  models: string[];
  has_secret?: boolean;
};

export type ProviderUpdateInput = {
  kind: ProviderKind;
  name: string;
  base_url: string;
  models: string[];
  locality: ProviderLocality;
  api_key?: string;
};

export type ProviderCreateInput = ProviderUpdateInput;

export function listProviders(): Promise<{ providers: ProviderRow[] }> {
  return apiJson("/admin/providers");
}

export function createProvider(body: ProviderCreateInput): Promise<ProviderRow> {
  return apiJson("/admin/providers", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function updateProvider(
  id: string,
  body: ProviderUpdateInput,
): Promise<ProviderRow> {
  return apiJson(`/admin/providers/${id}`, {
    method: "PUT",
    body: JSON.stringify(body),
  });
}

export function deleteProvider(id: string): Promise<void> {
  return apiJson(`/admin/providers/${id}`, { method: "DELETE" });
}

export function testProvider(id: string): Promise<{ ok: boolean; error?: string }> {
  return apiJson(`/admin/providers/${id}/test`, { method: "POST" });
}
