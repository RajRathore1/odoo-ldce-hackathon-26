"use client";

import { useState } from "react";
import {
  ActivityIcon,
  BellIcon,
  ChartIcon,
  DashboardIcon,
  MapPinIcon,
  SearchIcon,
  UsersIcon,
} from "@/components/icons";
import { cn } from "@/lib/cn";
import { useActiveSection } from "@/lib/use-active-section";

function GlobeMark() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      className="size-8 shrink-0 rounded-xl bg-primary p-1.5 text-accent"
      aria-hidden
    >
      <circle cx="12" cy="12" r="9" />
      <path d="M3 12h18" />
      <path d="M12 3c2.5 2.6 3.8 5.6 3.8 9S14.5 18.4 12 21c-2.5-2.6-3.8-5.6-3.8-9S9.5 5.6 12 3Z" />
    </svg>
  );
}

function MenuIcon({ open }: { open: boolean }) {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      className="size-5"
      aria-hidden
    >
      {open ? (
        <path d="m5 5 10 10M15 5 5 15" />
      ) : (
        <path d="M3 6h14M3 10h14M3 14h14" />
      )}
    </svg>
  );
}

const navItems = [
  { id: "overview", label: "Overview", icon: DashboardIcon },
  { id: "cities", label: "Cities", icon: MapPinIcon },
  { id: "activities", label: "Activities", icon: ActivityIcon },
  { id: "analytics", label: "Analytics", icon: ChartIcon },
  { id: "users", label: "Users", icon: UsersIcon },
];

export function AdminShell({ children }: { children: React.ReactNode }) {
  const activeId = useActiveSection(navItems.map((item) => item.id));
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-subtle">
      <aside className="hidden w-60 shrink-0 flex-col border-r border-border bg-surface px-4 py-6 lg:flex">
        <div className="flex items-center gap-2 px-2">
          <GlobeMark />
          <span className="font-heading text-base font-semibold">
            GlobeTrotter
          </span>
        </div>

        <nav className="mt-8 flex-1 space-y-1">
          {navItems.map((item) => {
            const active = item.id === activeId;
            return (
              <a
                key={item.id}
                href={`#${item.id}`}
                aria-current={active ? "true" : undefined}
                className={cn(
                  "relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
                  active
                    ? "bg-primary/8 text-primary"
                    : "text-text-muted hover:bg-bg hover:text-text",
                )}
              >
                <span
                  className={cn(
                    "absolute left-0 h-5 w-0.5 rounded-full bg-primary transition-opacity",
                    active ? "opacity-100" : "opacity-0",
                  )}
                />
                <item.icon className="size-4" />
                {item.label}
              </a>
            );
          })}
        </nav>

        <div className="rounded-xl bg-bg p-3 text-xs text-text-muted">
          Signed in as <span className="font-medium text-text">Admin</span>
        </div>
      </aside>

      <div className="min-w-0 flex-1">
        <header className="sticky top-0 z-20 border-b border-border bg-surface/95 backdrop-blur">
          <div className="flex items-center gap-2 px-4 py-3 sm:gap-4 sm:px-6">
            <button
              type="button"
              onClick={() => setMobileNavOpen((current) => !current)}
              aria-label="Toggle navigation"
              aria-expanded={mobileNavOpen}
              className="-ml-1 rounded-lg p-2 text-text-muted transition-colors hover:bg-bg lg:hidden"
            >
              <MenuIcon open={mobileNavOpen} />
            </button>

            <div className="relative max-w-sm flex-1">
              <SearchIcon className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-text-muted" />
              <input
                type="search"
                placeholder="Search anything"
                aria-label="Search"
                className="w-full rounded-full border border-border bg-bg py-2 pr-4 pl-9 text-sm placeholder:text-text-muted/70 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/15"
              />
            </div>

            <button
              type="button"
              className="relative rounded-full p-2 text-text-muted transition-colors hover:bg-bg"
              aria-label="Notifications"
            >
              <BellIcon className="size-5" />
              <span className="absolute top-1.5 right-1.5 size-1.5 rounded-full bg-accent" />
            </button>

            <div className="flex items-center gap-2 border-l border-border pl-3 sm:pl-4">
              <span className="flex size-8 items-center justify-center rounded-full bg-primary/10 text-sm font-semibold text-primary">
                A
              </span>
              <div className="hidden text-sm sm:block">
                <p className="font-medium">Admin</p>
                <p className="text-xs text-text-muted">Super admin</p>
              </div>
            </div>
          </div>

          {mobileNavOpen && (
            <nav className="space-y-1 border-t border-border bg-surface px-4 py-3 lg:hidden">
              {navItems.map((item) => {
                const active = item.id === activeId;
                return (
                  <a
                    key={item.id}
                    href={`#${item.id}`}
                    onClick={() => setMobileNavOpen(false)}
                    aria-current={active ? "true" : undefined}
                    className={cn(
                      "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
                      active
                        ? "bg-primary/8 text-primary"
                        : "text-text-muted hover:bg-bg hover:text-text",
                    )}
                  >
                    <item.icon className="size-4" />
                    {item.label}
                  </a>
                );
              })}
            </nav>
          )}
        </header>

        <main className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6 sm:py-10">
          {children}
        </main>
      </div>
    </div>
  );
}
