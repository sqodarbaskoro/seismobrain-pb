/**
 * @file users.ts
 * @description Typed calls for admin user management: approve/disable/role/sign-out
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

export type UserRow = {
  id: string;
  email: string;
  name: string;
  status: "pending" | "active" | "disabled" | string;
  system_role: "system_admin" | "user" | string;
};

export function listUsers(): Promise<{ users: UserRow[] }> {
  return apiJson("/admin/users");
}

export function approveUser(id: string): Promise<{ id: string; status: string }> {
  return apiJson(`/admin/users/${id}/approve`, { method: "POST" });
}

export function disableUser(id: string): Promise<{ id: string; status: string }> {
  return apiJson(`/admin/users/${id}/disable`, { method: "POST" });
}

export function setUserRole(
  id: string,
  system_role: "system_admin" | "user",
): Promise<{ id: string; system_role: string }> {
  return apiJson(`/admin/users/${id}/role`, {
    method: "POST",
    body: JSON.stringify({ system_role }),
  });
}

export function forceSignOut(id: string): Promise<{ revoked_families: number }> {
  return apiJson(`/admin/users/${id}/sessions/revoke`, { method: "POST" });
}
