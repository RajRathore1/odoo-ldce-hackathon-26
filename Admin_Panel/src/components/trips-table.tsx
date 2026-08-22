"use client";

import { useMemo, useState } from "react";
import { SearchIcon } from "@/components/icons";
import { deleteAdminTrip, type AdminApiTrip } from "@/lib/admin-api";
import { cn } from "@/lib/cn";

const statusTone: Record<AdminApiTrip["status"], string> = {
  DRAFT: "bg-subtle text-text-muted",
  PLANNED: "bg-info/12 text-info",
  ONGOING: "bg-warning/15 text-warning",
  COMPLETED: "bg-success/12 text-success",
  CANCELLED: "bg-danger/12 text-danger",
};

const money = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

const dateFormatter = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "short",
  timeZone: "UTC",
});

export function TripsTable({
  trips,
  onDeleted,
}: {
  trips: AdminApiTrip[];
  onDeleted: (id: number) => void;
}) {
  const [search, setSearch] = useState("");
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const rows = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return trips;
    return trips.filter((trip) =>
      [trip.name, trip.user_email].some((field) =>
        field.toLowerCase().includes(query),
      ),
    );
  }, [trips, search]);

  async function handleDelete(trip: AdminApiTrip) {
    if (!window.confirm(`Remove "${trip.name}"? This soft-deletes the trip.`)) {
      return;
    }

    setDeletingId(trip.id);
    try {
      await deleteAdminTrip(trip.id);
      onDeleted(trip.id);
    } catch {
      setDeletingId(null);
    }
  }

  return (
    <div className="space-y-4">
      <div className="relative">
        <SearchIcon className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-text-muted" />
        <input
          type="search"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search by trip name or traveller email"
          aria-label="Search trips"
          className="w-full rounded-xl border border-border bg-surface py-2 pr-3 pl-9 text-sm text-text placeholder:text-text-muted/70 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/15"
        />
      </div>

      <div className="overflow-x-auto rounded-xl border border-border">
        <table className="w-full text-left text-sm">
          <thead className="bg-subtle text-xs font-medium text-text-muted">
            <tr>
              <th className="px-4 py-3">Trip</th>
              <th className="px-4 py-3">Traveller</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Dates</th>
              <th className="px-4 py-3">Budget</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {rows.map((trip) => (
              <tr key={trip.id} className="transition-colors hover:bg-subtle">
                <td className="px-4 py-3 font-medium whitespace-nowrap">
                  {trip.name}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-text-muted">
                  {trip.user_email}
                </td>
                <td className="px-4 py-3">
                  <span
                    className={cn(
                      "inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium",
                      statusTone[trip.status],
                    )}
                  >
                    {trip.status}
                  </span>
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-text-muted">
                  {dateFormatter.format(new Date(`${trip.start_date}T00:00:00Z`))} –{" "}
                  {dateFormatter.format(new Date(`${trip.end_date}T00:00:00Z`))}
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  {trip.total_budget ? money.format(Number(trip.total_budget)) : "—"}
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <button
                    type="button"
                    onClick={() => handleDelete(trip)}
                    disabled={deletingId === trip.id}
                    className="rounded-full border border-border px-3 py-1 text-xs font-medium text-text-muted transition-colors hover:border-danger/40 hover:text-danger disabled:opacity-50"
                  >
                    {deletingId === trip.id ? "Removing…" : "Remove"}
                  </button>
                </td>
              </tr>
            ))}

            {rows.length === 0 && (
              <tr>
                <td
                  colSpan={6}
                  className="px-4 py-8 text-center text-text-muted"
                >
                  No trips match this search.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
