"use client";

import { useMemo, useState } from "react";
import { RegionCard } from "@/components/region-card";
import { SearchFilterBar } from "@/components/search-filter-bar";
import { SectionHeader } from "@/components/section-header";
import { TripCard } from "@/components/trip-card";
import { regions } from "@/lib/mock-data";
import {
  filterByStatus,
  groupOptions,
  groupTrips,
  searchTrips,
  sortOptions,
  sortTrips,
  statusFilters,
} from "@/lib/trips";
import type { Trip } from "@/lib/types";

export function LandingExplorer({ trips }: { trips: Trip[] }) {
  const [search, setSearch] = useState("");
  const [group, setGroup] = useState("none");
  const [status, setStatus] = useState("all");
  const [order, setOrder] = useState("newest");

  const visibleRegions = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return regions;

    return regions.filter((region) =>
      [region.name, region.country, region.blurb].some((field) =>
        field.toLowerCase().includes(query),
      ),
    );
  }, [search]);

  const groups = useMemo(() => {
    const matched = sortTrips(
      filterByStatus(searchTrips(trips, search), status),
      order,
    );
    return groupTrips(matched, group);
  }, [trips, search, status, order, group]);

  const matchCount = groups.reduce((total, bucket) => total + bucket.trips.length, 0);
  const searching = search.trim().length > 0;

  return (
    <div className="space-y-12">
      <SearchFilterBar
        search={search}
        onSearchChange={setSearch}
        placeholder="Search a place, country or trip"
        groupBy={{ value: group, onChange: setGroup, options: groupOptions }}
        filter={{ value: status, onChange: setStatus, options: statusFilters }}
        sortBy={{ value: order, onChange: setOrder, options: sortOptions }}
      />

      <section>
        <SectionHeader
          title="Top regional selections"
          description="Places other GlobeTrotters are planning around right now."
          action={{ label: "See all", href: "/explore" }}
        />

        {visibleRegions.length > 0 ? (
          <div className="-mx-4 flex snap-x gap-4 overflow-x-auto px-4 pb-2 sm:mx-0 sm:px-0">
            {visibleRegions.map((region) => (
              <RegionCard key={region.id} region={region} />
            ))}
          </div>
        ) : (
          <EmptyState message={`No regions match “${search.trim()}”.`} />
        )}
      </section>

      <section>
        <SectionHeader
          title="Previous trips"
          description={
            searching
              ? `${matchCount} of ${trips.length} trips match your search.`
              : "Pick one up again, or copy it into something new."
          }
          action={{ label: "See all", href: "/trips" }}
        />

        {matchCount > 0 ? (
          <div className="space-y-8">
            {groups.map((bucket) => (
              <div key={bucket.label || "all"}>
                {bucket.label && (
                  <h3 className="mb-3 text-sm font-semibold text-text-muted">
                    {bucket.label}
                  </h3>
                )}
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {bucket.trips.map((trip) => (
                    <TripCard
                      key={trip.id}
                      trip={trip}
                      href={`/trips/${trip.id}`}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState message="No trips match those filters yet." />
        )}
      </section>
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="rounded-2xl border border-dashed border-border bg-subtle px-6 py-12 text-center text-sm text-text-muted">
      {message}
    </div>
  );
}
