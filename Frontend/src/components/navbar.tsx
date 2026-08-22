"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { cn } from "@/lib/cn";
import { useAuth } from "@/components/auth-provider";
import { Avatar } from "@/components/ui/avatar";
import { Button, buttonStyles } from "@/components/ui/button";

const links = [
  { href: "/", label: "Home" },
  { href: "/trips", label: "My Trips" },
  { href: "/explore", label: "Explore" },
  { href: "/community", label: "Community" },
  { href: "/calendar", label: "Calendar" },
];

type NavUser = { name: string; avatar: string | null };

export function GlobalTrotterNavbar({ user }: { user: NavUser }) {
  const pathname = usePathname();
  const { signOut } = useAuth();
  const [open, setOpen] = useState(false);
  const [signingOut, setSigningOut] = useState(false);

  const isActive = (href: string) =>
    href === "/" ? pathname === "/" : pathname.startsWith(href);

  async function handleSignOut() {
    setSigningOut(true);
    await signOut();
  }

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-surface/95 backdrop-blur">
      <div className="mx-auto flex h-16 w-full max-w-6xl items-center gap-4 px-4 sm:px-6">
        <Link href="/" className="flex items-center gap-2">
          <GlobeMark />
          <span className="font-heading text-lg font-semibold text-primary">
            GlobeTrotter
          </span>
        </Link>

        <nav className="ml-6 hidden items-center gap-1 md:flex">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "rounded-full px-3.5 py-2 text-sm font-medium transition-colors",
                isActive(link.href)
                  ? "bg-primary text-white"
                  : "text-text-muted hover:bg-subtle hover:text-text",
              )}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="ml-auto flex items-center gap-3">
          <Link
            href="/trips/new"
            className={buttonStyles("accent", "sm", "hidden sm:inline-flex")}
          >
            Plan a trip
          </Link>

          <Link href="/profile" aria-label="Your profile" title={user.name}>
            <Avatar name={user.name} src={user.avatar} size="sm" />
          </Link>

          <Button
            variant="ghost"
            size="sm"
            onClick={handleSignOut}
            disabled={signingOut}
            className="hidden md:inline-flex"
          >
            {signingOut ? "Signing out..." : "Sign out"}
          </Button>

          <button
            type="button"
            aria-label="Toggle navigation"
            aria-expanded={open}
            onClick={() => setOpen((value) => !value)}
            className="-mr-1 rounded-lg p-2 text-text-muted hover:bg-subtle md:hidden"
          >
            <MenuIcon open={open} />
          </button>
        </div>
      </div>

      {open && (
        <nav className="border-t border-border bg-surface px-4 py-2 md:hidden">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setOpen(false)}
              className={cn(
                "block rounded-xl px-3 py-2.5 text-sm font-medium",
                isActive(link.href)
                  ? "bg-primary text-white"
                  : "text-text-muted",
              )}
            >
              {link.label}
            </Link>
          ))}
          <Link
            href="/trips/new"
            onClick={() => setOpen(false)}
            className={buttonStyles("accent", "sm", "my-2 w-full sm:hidden")}
          >
            Plan a trip
          </Link>
          <Button
            variant="outline"
            size="sm"
            onClick={handleSignOut}
            disabled={signingOut}
            className="mb-2 w-full"
          >
            {signingOut ? "Signing out..." : "Sign out"}
          </Button>
        </nav>
      )}
    </header>
  );
}

export function GlobeMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      className={cn("size-7 text-accent", className)}
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
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      className="size-5"
      aria-hidden
    >
      {open ? (
        <path d="m6 6 12 12M18 6 6 18" />
      ) : (
        <path d="M4 7h16M4 12h16M4 17h16" />
      )}
    </svg>
  );
}
