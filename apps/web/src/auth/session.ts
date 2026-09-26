/**
 * @file session.ts
 * @description In-memory + sessionStorage auth session for Starter SPA
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-17
 * @version 0.1.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { create } from "zustand";

const ACCESS_KEY = "sb_access_token";
const CSRF_KEY = "sb_csrf_token";

export type AuthUser = {
  id: string;
  email: string | null;
  name: string | null;
  system_role: "system_admin" | "user";
};

type SessionState = {
  accessToken: string | null;
  csrfToken: string | null;
  user: AuthUser | null;
  setTokens: (accessToken: string, csrfToken: string) => void;
  setUser: (user: AuthUser | null) => void;
  clear: () => void;
};

function readStored(key: string): string | null {
  try {
    return sessionStorage.getItem(key);
  } catch {
    return null;
  }
}

function writeStored(key: string, value: string | null): void {
  try {
    if (value === null) sessionStorage.removeItem(key);
    else sessionStorage.setItem(key, value);
  } catch {
    // private mode / unavailable storage
  }
}

export const useSession = create<SessionState>((set) => ({
  accessToken: readStored(ACCESS_KEY),
  csrfToken: readStored(CSRF_KEY),
  user: null,
  setTokens: (accessToken, csrfToken) => {
    writeStored(ACCESS_KEY, accessToken);
    writeStored(CSRF_KEY, csrfToken);
    set({ accessToken, csrfToken });
  },
  setUser: (user) => set({ user }),
  clear: () => {
    writeStored(ACCESS_KEY, null);
    writeStored(CSRF_KEY, null);
    set({ accessToken: null, csrfToken: null, user: null });
  },
}));

export function getAccessToken(): string | null {
  return useSession.getState().accessToken;
}

export function getCsrfToken(): string | null {
  return useSession.getState().csrfToken;
}
