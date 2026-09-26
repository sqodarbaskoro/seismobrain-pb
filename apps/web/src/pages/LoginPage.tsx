/**
 * @file LoginPage.tsx
 * @description Email/password login for Starter SPA
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-17
 * @version 0.1.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { FormEvent, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { ApiError, login } from "@/api/client";

export function LoginPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await login(email.trim(), password);
      const next = params.get("next") || "/onboarding";
      navigate(next);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main
      className="mx-auto flex min-h-screen max-w-md flex-col justify-center gap-4 px-6"
      data-testid="login-page"
    >
      <h1 className="text-3xl font-semibold tracking-tight">Sign in</h1>
      <p className="text-sm text-foreground/70">SeismoBrain Starter</p>
      <form className="space-y-3" onSubmit={onSubmit} aria-label="Login form">
        <label className="block text-sm" htmlFor="login-email">
          Email
        </label>
        <input
          id="login-email"
          type="email"
          required
          autoComplete="username"
          className="w-full rounded border border-border bg-background px-3 py-2"
          value={email}
          onChange={(ev) => setEmail(ev.target.value)}
        />
        <label className="block text-sm" htmlFor="login-password">
          Password
        </label>
        <input
          id="login-password"
          type="password"
          required
          minLength={12}
          autoComplete="current-password"
          className="w-full rounded border border-border bg-background px-3 py-2"
          value={password}
          onChange={(ev) => setPassword(ev.target.value)}
        />
        {error ? (
          <p role="alert" className="text-sm text-destructive" data-testid="login-error">
            {error}
          </p>
        ) : null}
        <button
          type="submit"
          disabled={busy}
          className="w-full rounded bg-primary px-4 py-2 text-primary-foreground disabled:opacity-60"
        >
          {busy ? "Signing in…" : "Sign in"}
        </button>
      </form>
      <p className="text-sm">
        Need an account?{" "}
        <Link className="underline" to="/register">
          Register
        </Link>
      </p>
    </main>
  );
}
