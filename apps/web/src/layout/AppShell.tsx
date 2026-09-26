/**
 * @file AppShell.tsx
 * @description Authenticated product chrome: a left sidebar (primary nav + admin groups),
 * collapsible to a hamburger-triggered panel below md
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-26
 * @version 0.7.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { Menu, Moon, Sun, X } from "lucide-react";
import { useState, type ReactNode } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useSession } from "@/auth/session";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useTheme } from "@/lib/theme";

const linkClass = ({ isActive }: { isActive: boolean }) =>
  cn(
    "flex items-center whitespace-nowrap rounded-md px-2.5 py-1.5 text-sm",
    isActive ? "bg-primary/15 font-medium text-primary" : "text-foreground/80 hover:bg-foreground/5",
  );

/** One labeled cluster of admin nav links, e.g. "People & Access" or "System". */
function NavGroup({
  label,
  testId,
  children,
}: {
  label: string;
  testId: string;
  children: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1" data-testid={testId}>
      <span className="px-2.5 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
        {label}
      </span>
      <div className="flex flex-col gap-0.5" aria-label={label}>
        {children}
      </div>
    </div>
  );
}

export function AppShell() {
  const navigate = useNavigate();
  const user = useSession((s) => s.user);
  const clear = useSession((s) => s.clear);
  const isAdmin = user?.system_role === "system_admin";
  const { theme, toggleTheme } = useTheme();
  const [mobileOpen, setMobileOpen] = useState(false);

  function signOut() {
    clear();
    navigate("/login", { replace: true });
  }

  return (
    <div data-testid="app-shell" className="flex min-h-screen flex-col md:flex-row">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded focus:bg-primary focus:px-3 focus:py-2 focus:text-sm focus:text-primary-foreground"
      >
        Skip to main content
      </a>

      {/* Mobile-only top bar: the sidebar below lives behind this hamburger under md. */}
      <div className="sticky top-0 z-40 flex items-center gap-3 border-b border-border bg-[hsl(var(--background))]/95 px-4 py-2 backdrop-blur md:hidden">
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="h-8 w-8 px-0"
          aria-expanded={mobileOpen}
          aria-controls="app-shell-panel"
          aria-label={mobileOpen ? "Close menu" : "Open menu"}
          onClick={() => setMobileOpen((open) => !open)}
        >
          {mobileOpen ? (
            <X className="h-4 w-4" aria-hidden="true" />
          ) : (
            <Menu className="h-4 w-4" aria-hidden="true" />
          )}
        </Button>
        <NavLink to="/" className="text-sm font-semibold tracking-tight text-primary" end>
          SeismoBrain
        </NavLink>
      </div>

      <aside
        id="app-shell-panel"
        className={cn(
          "flex-col border-b border-border md:sticky md:top-0 md:h-screen md:w-64 md:shrink-0 md:border-b-0 md:border-r md:bg-background",
          mobileOpen ? "flex" : "hidden md:flex",
        )}
      >
        <div className="hidden items-center px-4 py-3 md:flex">
          <NavLink to="/" className="text-sm font-semibold tracking-tight text-primary" end>
            SeismoBrain
          </NavLink>
        </div>

        <nav className="flex flex-col gap-1 p-3" aria-label="Primary" data-testid="primary-nav">
          <NavLink to="/chat" className={linkClass}>
            Chat
          </NavLink>
          <NavLink to="/library" className={linkClass}>
            Documents
          </NavLink>
        </nav>

        {isAdmin ? (
          <nav
            className="flex flex-col gap-4 overflow-y-auto border-t border-border p-3"
            id="admin-nav"
            data-testid="admin-nav"
            aria-label="Admin"
          >
            <NavGroup label="People & Access" testId="admin-nav-people">
              <NavLink to="/people/users" className={linkClass}>
                Users
              </NavLink>
              <NavLink to="/people/teams" className={linkClass}>
                Teams
              </NavLink>
            </NavGroup>
            <NavGroup label="Settings" testId="admin-nav-settings">
              <NavLink to="/settings/providers" className={linkClass}>
                Providers
              </NavLink>
              <NavLink to="/settings/workspaces" className={linkClass}>
                Workspaces
              </NavLink>
              <NavLink to="/settings/glossary" className={linkClass}>
                Dictionary
              </NavLink>
              <NavLink to="/settings/quarantine" className={linkClass}>
                Files needing review
              </NavLink>
              <NavLink to="/onboarding" className={linkClass}>
                Guided setup
              </NavLink>
            </NavGroup>
            <NavGroup label="System" testId="admin-nav-system">
              <NavLink to="/system/status" className={linkClass}>
                Status
              </NavLink>
              <NavLink to="/system/ingestion" className={linkClass}>
                Ingestion
              </NavLink>
              <NavLink to="/system/metrics" className={linkClass}>
                Metrics
              </NavLink>
            </NavGroup>
          </nav>
        ) : null}

        <div className="mt-auto flex flex-col gap-2 border-t border-border p-3 text-sm">
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-8 w-8 px-0"
              onClick={toggleTheme}
              aria-label="Toggle theme"
            >
              {theme === "dark" ? (
                <Sun className="h-4 w-4" aria-hidden="true" />
              ) : (
                <Moon className="h-4 w-4" aria-hidden="true" />
              )}
            </Button>
            <NavLink to="/account" className={(props) => cn(linkClass(props), "flex-1")}>
              Account
            </NavLink>
          </div>
          {user?.email ? (
            <span className="truncate px-0.5 text-xs text-muted-foreground" title={user.email}>
              {user.email}
            </span>
          ) : null}
          <Button type="button" variant="outline" size="sm" className="h-8" onClick={signOut} data-testid="sign-out">
            Sign out
          </Button>
        </div>
      </aside>

      <div id="main-content" className="min-w-0 flex-1" tabIndex={-1}>
        <Outlet />
      </div>
    </div>
  );
}
