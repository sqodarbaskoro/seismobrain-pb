/**
 * @file LandingPage.tsx
 * @description Product start hub: guest entry CTAs + signed-in links to core features
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-17
 * @version 0.1.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchAuthStatus, loadMe } from "@/api/client";
import { useSession } from "@/auth/session";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type HubLink = {
  to: string;
  title: string;
  description: string;
  adminOnly?: boolean;
};

const START_LINKS: HubLink[] = [
  {
    to: "/onboarding",
    title: "Guided setup",
    description: "Connect an AI provider, create a workspace, and load documents.",
    adminOnly: true,
  },
  {
    to: "/chat",
    title: "Chat",
    description: "Ask questions grounded in your documents with verifiable citations.",
  },
  {
    to: "/library",
    title: "Documents",
    description: "Browse collections, upload files, and review what has been indexed.",
  },
];

const ADMIN_LINKS: HubLink[] = [
  {
    to: "/settings/providers",
    title: "Providers",
    description: "Manage LLM connections used to write answers.",
    adminOnly: true,
  },
  {
    to: "/settings/workspaces",
    title: "Workspaces",
    description: "Organize collections and who can read or write them.",
    adminOnly: true,
  },
  {
    to: "/system/status",
    title: "System status",
    description: "Check whether the app and background services are healthy.",
    adminOnly: true,
  },
  {
    to: "/people/users",
    title: "Users",
    description: "Approve accounts and manage system roles.",
    adminOnly: true,
  },
  {
    to: "/account",
    title: "Account",
    description: "Review your profile and API tokens.",
  },
];

function HubCard({ link }: { link: HubLink }) {
  return (
    <Link
      to={link.to}
      className="block rounded-lg outline-none ring-offset-background transition hover:border-primary/40 focus-visible:ring-2 focus-visible:ring-ring"
      data-testid={`hub-link-${link.to.replace(/\W+/g, "-")}`}
    >
      <Card className="h-full border-border transition hover:bg-accent/40">
        <CardHeader>
          <CardTitle className="text-base">{link.title}</CardTitle>
          <CardDescription>{link.description}</CardDescription>
        </CardHeader>
      </Card>
    </Link>
  );
}

export function LandingPage() {
  const token = useSession((s) => s.accessToken);
  const user = useSession((s) => s.user);
  const isAdmin = user?.system_role === "system_admin";
  const [firstAdmin, setFirstAdmin] = useState(false);

  useEffect(() => {
    if (token && !user) {
      void loadMe().catch(() => undefined);
    }
  }, [token, user]);

  useEffect(() => {
    if (token) return;
    fetchAuthStatus()
      .then((s) => setFirstAdmin(!s.has_users))
      .catch(() => setFirstAdmin(false));
  }, [token]);

  const startLinks = START_LINKS.filter((l) => !l.adminOnly || isAdmin);
  const adminLinks = ADMIN_LINKS.filter((l) => !l.adminOnly || isAdmin);

  return (
    <main
      className="mx-auto flex min-h-screen max-w-5xl flex-col gap-10 px-6 py-12"
      data-testid="landing-page"
    >
      <header className="space-y-4">
        <p className="text-sm uppercase tracking-[0.2em] text-primary">SeismoBrain</p>
        <h1 className="max-w-2xl text-4xl font-semibold tracking-tight md:text-5xl">
          Grounded document answers
        </h1>
        <p className="max-w-2xl text-base text-foreground/70">
          Self-hosted retrieval with citations you can verify. Start by signing in, run guided
          setup if you are an admin, then chat against your documents.
        </p>

        {!token ? (
          <div className="flex flex-wrap gap-3 pt-2">
            <Link
              to="/login"
              className="inline-flex h-10 items-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground"
            >
              Sign in
            </Link>
            <Link
              to="/register"
              className="inline-flex h-10 items-center rounded-md border border-border px-4 text-sm font-medium"
            >
              {firstAdmin ? "Create first admin" : "Register"}
            </Link>
          </div>
        ) : (
          <div className="flex flex-wrap items-center gap-3 pt-2 text-sm text-foreground/70">
            <span>
              Signed in as <strong className="text-foreground">{user?.email ?? "…"}</strong>
            </span>
            <Link to="/chat" className="font-medium text-primary underline-offset-4 hover:underline">
              Jump to chat
            </Link>
          </div>
        )}
      </header>

      {!token ? (
        <section className="space-y-4" aria-labelledby="how-to-start">
          <h2 id="how-to-start" className="text-lg font-semibold tracking-tight">
            How to get started
          </h2>
          <ol className="grid gap-3 md:grid-cols-3">
            <li className="rounded-lg border border-border bg-card p-4 text-sm">
              <p className="font-medium">1. Create or sign in</p>
              <p className="mt-1 text-muted-foreground">
                The first account becomes system admin. Later users may need approval.
              </p>
            </li>
            <li className="rounded-lg border border-border bg-card p-4 text-sm">
              <p className="font-medium">2. Run guided setup</p>
              <p className="mt-1 text-muted-foreground">
                Connect an AI provider, create a workspace, and add documents.
              </p>
            </li>
            <li className="rounded-lg border border-border bg-card p-4 text-sm">
              <p className="font-medium">3. Ask in chat</p>
              <p className="mt-1 text-muted-foreground">
                Answers cite evidence from your library. Open Documents anytime to manage files.
              </p>
            </li>
          </ol>
          <p className="text-sm text-muted-foreground">
            After you sign in, this page becomes a hub with links to Chat, Documents, Guided setup,
            Providers, Workspaces, Status, and more.
          </p>
        </section>
      ) : (
        <>
          <section className="space-y-4" aria-labelledby="start-here">
            <h2 id="start-here" className="text-lg font-semibold tracking-tight">
              Start here
            </h2>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {startLinks.map((link) => (
                <HubCard key={link.to} link={link} />
              ))}
            </div>
          </section>

          <section className="space-y-4" aria-labelledby="more-tools">
            <h2 id="more-tools" className="text-lg font-semibold tracking-tight">
              {isAdmin ? "Admin & settings" : "Your account"}
            </h2>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {adminLinks.map((link) => (
                <HubCard key={link.to} link={link} />
              ))}
            </div>
          </section>
        </>
      )}
    </main>
  );
}
