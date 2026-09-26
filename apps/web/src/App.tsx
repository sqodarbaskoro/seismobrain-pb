/**
 * @file App.tsx
 * @description Root SeismoBrain web shell with auth-gated routes and product nav
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-16
 * @modified 2026-09-17
 * @version 0.8.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Outlet, Route, Routes } from "react-router-dom";
import { RequireAuth } from "@/auth/RequireAuth";
import { Toaster } from "@/components/ui/sonner";
import { AppShell } from "@/layout/AppShell";
import { ThemeProvider } from "@/lib/theme";
import { AccountPage } from "@/pages/AccountPage";
import { AdminAnalyticsPage } from "@/pages/AdminAnalyticsPage";
import { AdminIngestionPage } from "@/pages/AdminIngestionPage";
import { AdminProvidersPage } from "@/pages/AdminProvidersPage";
import { AdminUsersPage } from "@/pages/AdminUsersPage";
import { AdminWorkspacesPage } from "@/pages/AdminWorkspacesPage";
import { ChatPage } from "@/pages/ChatPage";
import { DocumentsPage } from "@/pages/DocumentsPage";
import { GlossaryPage } from "@/pages/GlossaryPage";
import { LandingPage } from "@/pages/LandingPage";
import { LoginPage } from "@/pages/LoginPage";
import { OnboardingWizard } from "@/pages/OnboardingWizard";
import { PathTemplateTester } from "@/pages/PathTemplateTester";
import { QuarantinePage } from "@/pages/QuarantinePage";
import { RegisterPage } from "@/pages/RegisterPage";
import { SystemStatusPage } from "@/pages/SystemStatusPage";
import { TeamsPage } from "@/pages/TeamsPage";

const queryClient = new QueryClient();

function AuthedLayout() {
  return (
    <RequireAuth>
      <AppShell />
    </RequireAuth>
  );
}

/** Extra gate nested inside AuthedLayout: admin-only sections need the role check too. */
function AdminOnly() {
  return (
    <RequireAuth role="system_admin">
      <Outlet />
    </RequireAuth>
  );
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route element={<AuthedLayout />}>
              <Route path="/chat" element={<ChatPage />} />
              {/* "/library" not "/documents": the backend reserves the top-level "documents"
                  segment for its own API (see spa.py _API_ROOTS) — a page route there would
                  404 on a hard refresh in the real Starter server. */}
              <Route path="/library" element={<DocumentsPage />} />
              <Route path="/path-template" element={<PathTemplateTester />} />
              <Route path="/account" element={<AccountPage />} />
              <Route element={<AdminOnly />}>
                <Route path="/onboarding" element={<OnboardingWizard />} />
                {/* "/settings/*", "/people/*", "/system/*" not "/admin/*": same reason —
                    "admin" is a reserved API segment, these are not. */}
                <Route path="/settings/providers" element={<AdminProvidersPage />} />
                <Route path="/settings/workspaces" element={<AdminWorkspacesPage />} />
                <Route path="/settings/glossary" element={<GlossaryPage />} />
                <Route path="/settings/quarantine" element={<QuarantinePage />} />
                <Route path="/system/ingestion" element={<AdminIngestionPage />} />
                <Route path="/system/status" element={<SystemStatusPage />} />
                <Route path="/system/metrics" element={<AdminAnalyticsPage />} />
                <Route path="/people/users" element={<AdminUsersPage />} />
                <Route path="/people/teams" element={<TeamsPage />} />
              </Route>
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
        <Toaster />
      </ThemeProvider>
    </QueryClientProvider>
  );
}
