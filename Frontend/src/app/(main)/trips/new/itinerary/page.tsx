import Link from "next/link";
import { ItineraryBuilder } from "@/components/itinerary-builder";
import { buttonStyles } from "@/components/ui/button";
import { listCities } from "@/lib/api/geo-service";
import { getTripDto } from "@/lib/api/trips-service";

export default async function ItineraryBuilderPage({
  searchParams,
}: {
  searchParams: Promise<{ trip?: string }>;
}) {
  const { trip: tripId } = await searchParams;

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

  const [trip, cities] = await Promise.all([getTripDto(tripId), listCities()]);

  return (
    <ItineraryBuilder
      tripId={tripId}
      tripName={trip.name}
      tripStart={trip.start_date}
      tripEnd={trip.end_date}
      currency={trip.currency}
      cities={cities.map((city) => ({
        label: `${city.name}, ${city.country}`,
        value: city.id,
      }))}
    />
  );
}
