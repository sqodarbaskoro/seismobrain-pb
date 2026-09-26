/**
 * @file RegisterPage.tsx
 * @description Registration / first-admin bootstrap for Starter SPA
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-17
 * @version 0.1.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ApiError, fetchAuthStatus, login, registerUser } from "@/api/client";

export function RegisterPage() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [firstAdmin, setFirstAdmin] = useState(false);
  const [closed, setClosed] = useState(false);

  useEffect(() => {
    fetchAuthStatus()
      .then((s) => {
        setFirstAdmin(!s.has_users);
        setClosed(s.registration_mode === "closed");
      })
      .catch(() => {
        setError("Could not reach the API");
      });
  }, []);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setInfo(null);
    setBusy(true);
    try {
      const created = await registerUser({
        email: email.trim(),
        password,
        name: name.trim(),
      });
      if (created.status === "pending") {
        setInfo("Account created and awaits admin approval.");
        return;
      }
      await login(email.trim(), password);
      navigate(firstAdmin || created.system_role === "system_admin" ? "/onboarding" : "/chat");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Registration failed");
    } finally {
      setBusy(false);
    }
  }

  if (closed && !firstAdmin) {
    return (
      <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center gap-4 px-6">
        <h1 className="text-3xl font-semibold">Registration closed</h1>
        <p className="text-sm">Ask an administrator to create your account.</p>
        <Link className="underline" to="/login">
          Sign in
        </Link>
      </main>
    );
  }

  return (
    <main
      className="mx-auto flex min-h-screen max-w-md flex-col justify-center gap-4 px-6"
      data-testid="register-page"
    >
      <h1 className="text-3xl font-semibold tracking-tight">
        {firstAdmin ? "Create first admin" : "Register"}
      </h1>
      <p className="text-sm text-foreground/70">
        {firstAdmin
          ? "This first account becomes the system administrator."
          : "Create a SeismoBrain account."}
      </p>
      <form className="space-y-3" onSubmit={onSubmit} aria-label="Register form">
        <label className="block text-sm" htmlFor="reg-name">
          Name
        </label>
        <input
          id="reg-name"
          required
          className="w-full rounded border border-border bg-background px-3 py-2"
          value={name}
          onChange={(ev) => setName(ev.target.value)}
        />
        <label className="block text-sm" htmlFor="reg-email">
          Email
        </label>
        <input
          id="reg-email"
          type="email"
          required
          autoComplete="username"
          className="w-full rounded border border-border bg-background px-3 py-2"
          value={email}
          onChange={(ev) => setEmail(ev.target.value)}
        />
        <label className="block text-sm" htmlFor="reg-password">
          Password (min 12 characters)
        </label>
        <input
          id="reg-password"
          type="password"
          required
          minLength={12}
          autoComplete="new-password"
          className="w-full rounded border border-border bg-background px-3 py-2"
          value={password}
          onChange={(ev) => setPassword(ev.target.value)}
        />
        {error ? (
          <p role="alert" className="text-sm text-destructive" data-testid="register-error">
            {error}
          </p>
        ) : null}
        {info ? (
          <p role="status" className="text-sm text-success" data-testid="register-info">
            {info}
          </p>
        ) : null}
        <button
          type="submit"
          disabled={busy}
          className="w-full rounded bg-primary px-4 py-2 text-primary-foreground disabled:opacity-60"
        >
          {busy ? "Working…" : firstAdmin ? "Create admin" : "Register"}
        </button>
      </form>
      <p className="text-sm">
        Already have an account?{" "}
        <Link className="underline" to="/login">
          Sign in
        </Link>
      </p>
    </main>
  );
}
