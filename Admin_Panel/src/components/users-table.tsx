"use client";

import { useMemo, useState } from "react";
import { cn } from "@/lib/cn";
import type { AdminUser } from "@/lib/mock-data";

const dateFormatter = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "short",
  year: "numeric",
  timeZone: "UTC",
});

export function UsersTable({ users }: { users: AdminUser[] }) {
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return users;
    return users.filter((user) =>
      [user.name, user.email, user.city].some((field) =>
        field.toLowerCase().includes(query),
      ),
    );
  }, [users, search]);

  return (
    <div className="space-y-4">
      <input
        type="search"
        value={search}
        onChange={(event) => setSearch(event.target.value)}
        placeholder="Search by name, email or city"
        aria-label="Search users"
        className="w-full rounded-xl border border-border bg-surface px-3 py-2 text-sm text-text placeholder:text-text-muted/70 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/15"
      />

      <div className="overflow-x-auto rounded-xl border border-border">
        <table className="w-full text-left text-sm">
          <thead className="bg-subtle text-xs font-medium text-text-muted">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">City</th>
              <th className="px-4 py-3">Trips</th>
              <th className="px-4 py-3">Joined</th>
              <th className="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {filtered.map((user) => (
              <tr key={user.id} className="hover:bg-subtle/60">
                <td className="px-4 py-3 font-medium whitespace-nowrap">
                  {user.name}
                </td>
                <td className="px-4 py-3 text-text-muted whitespace-nowrap">
                  {user.email}
                </td>
                <td className="px-4 py-3 whitespace-nowrap">{user.city}</td>
                <td className="px-4 py-3">{user.trips}</td>
                <td className="px-4 py-3 whitespace-nowrap text-text-muted">
                  {dateFormatter.format(new Date(`${user.joined}T00:00:00Z`))}
                </td>
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
              </tr>
            ))}

            {filtered.length === 0 && (
              <tr>
                <td
                  colSpan={6}
                  className="px-4 py-8 text-center text-text-muted"
                >
                  No users match &quot;{search.trim()}&quot;.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
