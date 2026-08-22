"use client";

import { useMemo, useState } from "react";
import { SearchIcon } from "@/components/icons";
import { cn } from "@/lib/cn";
import type { AdminUser } from "@/lib/mock-data";

const dateFormatter = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "short",
  year: "numeric",
  timeZone: "UTC",
});

type StatusFilter = "all" | "active" | "suspended";
type SortKey = "name" | "trips" | "joined";
type SortDirection = "asc" | "desc";

const columns: { key: SortKey; label: string }[] = [
  { key: "name", label: "Name" },
  { key: "trips", label: "Trips" },
  { key: "joined", label: "Joined" },
];

function initials(name: string) {
  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0] ?? "")
    .join("")
    .toUpperCase();
}

export function UsersTable({ users }: { users: AdminUser[] }) {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<StatusFilter>("all");
  const [sortKey, setSortKey] = useState<SortKey>("joined");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");
  const [overrides, setOverrides] = useState<
    Record<string, "active" | "suspended">
  >({});

  function toggleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDirection((current) => (current === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDirection("asc");
    }
  }

  function toggleStatus(user: AdminUser) {
    const current = overrides[user.id] ?? user.status;
    const next = current === "active" ? "suspended" : "active";
    setOverrides((prev) => ({ ...prev, [user.id]: next }));
  }

  const effectiveUsers = useMemo(
    () => users.map((user) => ({ ...user, status: overrides[user.id] ?? user.status })),
    [users, overrides],
  );

  const rows = useMemo(() => {
    const query = search.trim().toLowerCase();
    const filtered = effectiveUsers.filter((user) => {
      const matchesQuery =
        !query ||
        [user.name, user.email, user.city].some((field) =>
          field.toLowerCase().includes(query),
        );
      const matchesStatus = status === "all" || user.status === status;
      return matchesQuery && matchesStatus;
    });

    const sorted = [...filtered].sort((a, b) => {
      const compared =
        sortKey === "name"
          ? a.name.localeCompare(b.name)
          : sortKey === "trips"
            ? a.trips - b.trips
            : a.joined.localeCompare(b.joined);
      return sortDirection === "asc" ? compared : -compared;
    });

    return sorted;
  }, [effectiveUsers, search, status, sortKey, sortDirection]);

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <SearchIcon className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-text-muted" />
          <input
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search by name, email or city"
            aria-label="Search users"
            className="w-full rounded-xl border border-border bg-surface py-2 pr-3 pl-9 text-sm text-text placeholder:text-text-muted/70 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/15"
          />
        </div>

        <select
          value={status}
          onChange={(event) => setStatus(event.target.value as StatusFilter)}
          aria-label="Filter by status"
          className="cursor-pointer rounded-xl border border-border bg-surface px-3 py-2 text-sm text-text focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/15 sm:w-44"
        >
          <option value="all">All statuses</option>
          <option value="active">Active</option>
          <option value="suspended">Suspended</option>
        </select>
      </div>

      <div className="overflow-x-auto rounded-xl border border-border">
        <table className="w-full text-left text-sm">
          <thead className="bg-subtle text-xs font-medium text-text-muted">
            <tr>
              {columns.map((column) => (
                <th key={column.key} className="px-4 py-3">
                  <button
                    type="button"
                    onClick={() => toggleSort(column.key)}
                    className="inline-flex items-center gap-1 hover:text-text"
                  >
                    {column.label}
                    <SortArrow
                      active={sortKey === column.key}
                      direction={sortDirection}
                    />
                  </button>
                </th>
              ))}
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">City</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {rows.map((user) => (
              <tr
                key={user.id}
                className="transition-colors hover:bg-subtle"
              >
                <td className="px-4 py-3 font-medium whitespace-nowrap">
                  <div className="flex items-center gap-2.5">
                    <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                      {initials(user.name)}
                    </span>
                    {user.name}
                  </div>
                </td>
                <td className="px-4 py-3">{user.trips}</td>
                <td className="px-4 py-3 whitespace-nowrap text-text-muted">
                  {dateFormatter.format(new Date(`${user.joined}T00:00:00Z`))}
                </td>
                <td className="px-4 py-3 text-text-muted whitespace-nowrap">
                  {user.email}
                </td>
                <td className="px-4 py-3 whitespace-nowrap">{user.city}</td>
                <td className="px-4 py-3">
                  <span
                    className={cn(
                      "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium",
                      user.status === "active"
                        ? "bg-success/12 text-success"
                        : "bg-danger/12 text-danger",
                    )}
                  >
                    <span
                      className={cn(
                        "size-1.5 rounded-full",
                        user.status === "active" ? "bg-success" : "bg-danger",
                      )}
                    />
                    {user.status === "active" ? "Active" : "Suspended"}
                  </span>
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <button
                    type="button"
                    onClick={() => toggleStatus(user)}
                    className={cn(
                      "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
                      user.status === "active"
                        ? "border-border text-text-muted hover:border-danger/40 hover:text-danger"
                        : "border-success/30 bg-success/10 text-success hover:bg-success/15",
                    )}
                  >
                    {user.status === "active" ? "Suspend" : "Reactivate"}
                  </button>
                </td>
              </tr>
            ))}

            {rows.length === 0 && (
              <tr>
                <td
                  colSpan={7}
                  className="px-4 py-8 text-center text-text-muted"
                >
                  No users match these filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function SortArrow({
  active,
  direction,
}: {
  active: boolean;
  direction: SortDirection;
}) {
  return (
    <svg
      viewBox="0 0 12 12"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn(
        "size-3 transition-transform",
        active ? "text-primary" : "text-text-muted/40",
        active && direction === "desc" && "rotate-180",
      )}
      aria-hidden
    >
      <path d="M3 5l3-3 3 3M6 2v8" />
    </svg>
  );
}
