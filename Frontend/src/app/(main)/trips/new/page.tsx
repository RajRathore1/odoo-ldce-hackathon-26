"use client";

import { ErrorBlock, LoadingBlock } from "@/components/page-state";
import { TripDetailsForm } from "@/components/trip-details-form";
import { toRegion } from "@/lib/api/adapters";
import type { CityDto } from "@/lib/api/geo-service";
import type { Paginated } from "@/lib/api/trips-service";
import { useApi } from "@/lib/api/use-api";

export default function NewTripPage() {
  const { data, error, loading, reload } =
    useApi<Paginated<CityDto>>("/cities/?page_size=100");

  return (
    <div className="space-y-10">
      <div>
        <h1 className="font-heading text-3xl font-semibold sm:text-4xl">
          Plan a new trip
        </h1>
        <p className="mt-2 max-w-xl text-text-muted">
          Pick a place, block out your dates, then start pulling in the
          things you don&apos;t want to miss.
        </p>
      </div>

      {loading && <LoadingBlock label="Loading destinations" />}
      {error && <ErrorBlock message={error} onRetry={reload} />}
      {data && <TripDetailsForm cities={data.results.map(toRegion)} />}
    </div>
  );
}
