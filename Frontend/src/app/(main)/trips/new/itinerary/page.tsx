"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { ItineraryBuilder } from "@/components/itinerary-builder";
import { ErrorBlock, LoadingBlock } from "@/components/page-state";
import { buttonStyles } from "@/components/ui/button";
import type { CityDto } from "@/lib/api/geo-service";
import type { Paginated, TripDto } from "@/lib/api/trips-service";
import { useApi } from "@/lib/api/use-api";

function Builder() {
  const tripId = useSearchParams().get("trip");

  const trip = useApi<TripDto>(tripId ? `/trips/${tripId}/` : null);
  const cities = useApi<Paginated<CityDto>>("/cities/?page_size=100");

  // Sections are stops on a trip, so there is nothing to build without one.
  if (!tripId) {
    return (
      <div className="rounded-2xl border border-dashed border-border px-6 py-16 text-center">
        <h1 className="font-heading text-2xl font-semibold">
          Start with a trip
        </h1>
        <p className="mx-auto mt-2 max-w-sm text-text-muted">
          Sections hang off a trip&apos;s dates, so create the trip first and
          you&apos;ll land back here.
        </p>
        <Link href="/trips/new" className={buttonStyles("accent", "md", "mt-6")}>
          Plan a trip
        </Link>
      </div>
    );
  }

  if (trip.loading || cities.loading) {
    return <LoadingBlock label="Loading your trip" />;
  }
  if (trip.error) {
    return <ErrorBlock message={trip.error} onRetry={trip.reload} />;
  }
  if (!trip.data) return null;

  return (
    <ItineraryBuilder
      tripId={tripId}
      tripName={trip.data.name}
      tripStart={trip.data.start_date}
      tripEnd={trip.data.end_date}
      currency={trip.data.currency}
      cities={(cities.data?.results ?? []).map((city) => ({
        label: `${city.name}, ${city.country.name}`,
        value: String(city.id),
      }))}
    />
  );
}

export default function ItineraryBuilderPage() {
  return (
    <Suspense fallback={<LoadingBlock />}>
      <Builder />
    </Suspense>
  );
}
