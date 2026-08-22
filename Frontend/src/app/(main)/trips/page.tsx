"use client";

import { useMemo, useState } from "react";
import { SearchFilterBar } from "@/components/search-filter-bar";
import { TripCard } from "@/components/trip-card";
import { trips } from "@/lib/mock-data";
import {
  filterByStatus,
  searchTrips,
  sortOptions,
  sortTrips,
  statusFilters,
} from "@/lib/trips";
import type { TripStatus } from "@/lib/types";

const statusGroups: { key: TripStatus; label: string }[] = [
  { key: "ongoing", label: "Ongoing" },
  { key: "upcoming", label: "Up-coming" },
  { key: "completed", label: "Completed" },
];

export default function TripsPage() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [order, setOrder] = useState("newest");

  const visible = useMemo(
    () => sortTrips(filterByStatus(searchTrips(trips, search), status), order),
    [search, status, order],
  );

  const groups = statusGroups
    .filter((group) => status === "all" || status === group.key)
    .map((group) => ({
      ...group,
      trips: visible.filter((trip) => trip.status === group.key),
    }));

  const searching = search.trim().length > 0;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-heading text-3xl font-semibold sm:text-4xl">
          My trips
        </h1>
        <p className="mt-2 text-text-muted">
          {searching
            ? `${visible.length} of ${trips.length} trips match your search.`
            : "Everything you've planned, grouped by where it stands."}
        </p>
      </div>

      <SearchFilterBar
        search={search}
        onSearchChange={setSearch}
        placeholder="Search a trip, city or country"
        filter={{ value: status, onChange: setStatus, options: statusFilters }}
        sortBy={{ value: order, onChange: setOrder, options: sortOptions }}
      />

      <div className="space-y-10">
        {groups.map((group) => (
          <section key={group.key}>
            <h2 className="mb-4 inline-flex items-center gap-2 font-heading text-xl font-semibold sm:text-2xl">
              {group.label}
              <span className="rounded-full bg-bg px-2 py-0.5 text-sm font-normal text-text-muted">
                {group.trips.length}
              </span>
            </h2>

            {group.trips.length > 0 ? (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {group.trips.map((trip) => (
                  <TripCard
                    key={trip.id}
                    trip={trip}
                    href={`/trips/${trip.id}`}
                  />
                ))}
              </div>
            ) : (
              <p className="rounded-2xl border border-dashed border-border px-6 py-10 text-center text-sm text-text-muted">
                No {group.label.toLowerCase()} trips{" "}
                {searching ? "match your search." : "yet."}
              </p>
            )}
          </section>
        ))}
      </div>
    </div>
  );
}
