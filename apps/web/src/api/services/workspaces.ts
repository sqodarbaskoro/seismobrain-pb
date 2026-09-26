/**
 * @file workspaces.ts
 * @description Typed calls for admin workspace/collection management and ACLs
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-17
 * @version 0.2.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { apiJson } from "@/api/client";

export type WorkspaceRow = { id: string; name: string; research_enabled: boolean };
export type AclEntry = { principal?: string; user_id?: string; permission?: string };
export type CollectionRow = { id: string; name: string; workspace_id: string; acl: AclEntry[] };

/** A workspace the caller has a role in, with the collections they can read (named,
 * unlike the bare ids `GET /api/v1/collections` returns) — for the chat workspace
 * switcher, not the admin console. */
export type MyWorkspace = { id: string; name: string; collections: { id: string; name: string }[] };

export function listWorkspaces(): Promise<{ workspaces: WorkspaceRow[] }> {
  return apiJson("/admin/workspaces");
}

export function listMyWorkspaces(): Promise<{ workspaces: MyWorkspace[] }> {
  return apiJson("/api/v1/workspaces");
}

export function createWorkspace(name: string): Promise<{ id: string; name: string }> {
  return apiJson("/admin/workspaces", { method: "POST", body: JSON.stringify({ name }) });
}

export function listWorkspaceCollections(
  workspaceId: string,
): Promise<{ collections: CollectionRow[] }> {
  return apiJson(`/admin/workspaces/${workspaceId}/collections`);
}

export function createCollection(
  workspaceId: string,
  name: string,
): Promise<{ id: string; name: string; workspace_id: string }> {
  return apiJson(`/admin/workspaces/${workspaceId}/collections`, {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}

export function setCollectionAcl(
  collectionId: string,
  entries: AclEntry[],
): Promise<{ id: string; entries: AclEntry[] }> {
  return apiJson(`/admin/collections/${collectionId}/acl`, {
    method: "PUT",
    body: JSON.stringify({ entries }),
  });
}

export function setResearchEnabled(
  workspaceId: string,
  enabled: boolean,
): Promise<{ id: string; research_enabled: boolean }> {
  return apiJson(`/api/v1/admin/workspaces/${workspaceId}/research`, {
    method: "POST",
    body: JSON.stringify({ enabled }),
  });
}
