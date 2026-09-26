/**
 * @file glossary.ts
 * @description Typed calls for workspace glossary (dictionary) and identifier patterns
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

export type GlossaryEntry = { term: string; expansion: string };
export type IdentifierPattern = { name: string; pattern: string; confidence: string };
export type GlossaryState = {
  workspace_id: string;
  glossary: GlossaryEntry[];
  identifier_patterns: IdentifierPattern[];
};

export function getGlossary(workspaceId: string): Promise<GlossaryState> {
  return apiJson(`/api/v1/workspaces/${workspaceId}/glossary`);
}

export function putGlossary(
  workspaceId: string,
  entries: GlossaryEntry[],
): Promise<GlossaryState> {
  return apiJson(`/api/v1/workspaces/${workspaceId}/glossary`, {
    method: "PUT",
    body: JSON.stringify({ entries }),
  });
}

export function putIdentifierPatterns(
  workspaceId: string,
  patterns: IdentifierPattern[],
): Promise<GlossaryState> {
  return apiJson(`/api/v1/workspaces/${workspaceId}/identifier-patterns`, {
    method: "PUT",
    body: JSON.stringify({ patterns }),
  });
}
