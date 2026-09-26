/**
 * @file RequireAuth.tsx
 * @description Route gate that requires a valid access session and, optionally, a role
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-17
 * @version 0.2.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { ReactNode, useEffect, useState } from "react";
import { Link, Navigate, useLocation } from "react-router-dom";
import { loadMe } from "@/api/client";
import { useSession, type AuthUser } from "@/auth/session";

export function RequireAuth({
  children,
  role,
}: {
  children: ReactNode;
  /** When set, only a user whose system_role matches is allowed through. */
  role?: AuthUser["system_role"];
}) {
  const location = useLocation();
  const accessToken = useSession((s) => s.accessToken);
  const user = useSession((s) => s.user);
  const [ready, setReady] = useState(Boolean(user));
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (!accessToken) {
      setFailed(true);
      setReady(true);
      return;
    }
    if (user) {
      setReady(true);
      return;
    }
    let cancelled = false;
    loadMe()
      .then(() => {
        if (!cancelled) setReady(true);
      })
      .catch(() => {
        if (!cancelled) {
          setFailed(true);
          setReady(true);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken, user]);

  if (!ready) {
    return (
      <main className="flex min-h-screen items-center justify-center text-sm" aria-busy="true">
        Checking session…
      </main>
    );
  }
  if (!accessToken || failed) {
    return (
      <Navigate
        to={`/login?next=${encodeURIComponent(location.pathname)}`}
        replace
      />
    );
  }
  if (role && user?.system_role !== role) {
    return (
      <main
        className="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center gap-3 px-6 text-center"
        data-testid="access-denied"
      >
        <h1 className="text-lg font-semibold">You don't have access to this page</h1>
        <p className="text-sm text-muted-foreground">
          This section is only available to workspace admins. If you need access, ask an
          admin to change your role.
        </p>
        <Link to="/chat" className="text-sm text-primary underline underline-offset-4">
          Back to chat
        </Link>
      </main>
    );
  }
  return children;
}
