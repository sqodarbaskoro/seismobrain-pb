/**
 * @file groups.ts
 * @description Typed calls for teams (groups): membership and collection/document grants
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

export type GroupSummary = { id: string; name: string; tenant_id: string; member_count: number };
export type GroupDetail = { id: string; name: string; tenant_id: string; members: string[] };
export type Permission = "read" | "write" | "manage";
export type ResourceType = "collection" | "document";
export type ResourceGrant = { group_id: string; group_name: string; permission: Permission };

export function listGroups(): Promise<{ groups: GroupSummary[] }> {
  return apiJson("/api/v1/groups");
}

export function getGroup(groupId: string): Promise<GroupDetail> {
  return apiJson(`/api/v1/groups/${groupId}`);
}

export function createGroup(name: string): Promise<{ id: string; name: string }> {
  return apiJson("/api/v1/groups", { method: "POST", body: JSON.stringify({ name }) });
}

export function addMember(groupId: string, userId: string): Promise<{ members: string[] }> {
  return apiJson(`/api/v1/groups/${groupId}/members`, {
    method: "POST",
    body: JSON.stringify({ user_id: userId }),
  });
}

export function removeMember(groupId: string, userId: string): Promise<{ members: string[] }> {
  return apiJson(`/api/v1/groups/${groupId}/members/${userId}`, { method: "DELETE" });
}

export function listGrantsForResource(
  resourceType: ResourceType,
  resourceId: string,
): Promise<{ grants: ResourceGrant[] }> {
  const params = new URLSearchParams({ resource_type: resourceType, resource_id: resourceId });
  return apiJson(`/api/v1/groups/grants?${params.toString()}`);
}

export function grantPermission(
  groupId: string,
  resourceType: ResourceType,
  resourceId: string,
  permission: Permission,
): Promise<{ vector_sync_ok: boolean }> {
  return apiJson(`/api/v1/groups/${groupId}/grants`, {
    method: "POST",
    body: JSON.stringify({ resource_type: resourceType, resource_id: resourceId, permission }),
  });
}

export function revokeGrant(
  groupId: string,
  resourceType: ResourceType,
  resourceId: string,
): Promise<{ revoked: boolean }> {
  const params = new URLSearchParams({ resource_type: resourceType, resource_id: resourceId });
  return apiJson(`/api/v1/groups/${groupId}/grants?${params.toString()}`, { method: "DELETE" });
}
