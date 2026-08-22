"use client";

import { TripsBrowser } from "@/components/trips-browser";
import { ErrorBlock, LoadingBlock } from "@/components/page-state";
import { toTrip } from "@/lib/api/adapters";
import type { Paginated, TripDto } from "@/lib/api/trips-service";
import { useApi } from "@/lib/api/use-api";

export default function TripsPage() {
  const { data, error, loading, reload } =
    useApi<Paginated<TripDto>>("/trips/?page_size=100");

  if (loading) return <LoadingBlock label="Loading your trips" />;
  if (error) return <ErrorBlock message={error} onRetry={reload} />;

  return <TripsBrowser trips={(data?.results ?? []).map(toTrip)} />;
}
