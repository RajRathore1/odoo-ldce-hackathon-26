import { notFound } from "next/navigation";
import { ItineraryBudgetView } from "@/components/itinerary-budget-view";
import { StatusBadge } from "@/components/ui/badge";
import { ApiError } from "@/lib/api/envelope";
import { getItinerary, getTripDto, toTrip } from "@/lib/api/trips-service";
import { formatDateRange, formatMoney } from "@/lib/format";

export default async function TripItineraryPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  let trip;
  let days;

  try {
    const [dto, itinerary] = await Promise.all([
      getTripDto(id),
      getItinerary(id),
    ]);
    trip = toTrip(dto);
    days = itinerary;
  } catch (error) {
    if (error instanceof ApiError && [403, 404].includes(error.status)) {
      notFound();
    }
    throw error;
  }

  const place = [trip.city, trip.country].filter(Boolean).join(", ");

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          {place && (
            <p className="text-sm font-medium text-text-muted">{place}</p>
          )}
          <h1 className="mt-1 font-heading text-3xl font-semibold sm:text-4xl">
            {trip.title}
          </h1>
          <p className="mt-2 text-text-muted">
            {formatDateRange(trip.startDate, trip.endDate)} · {trip.stops}{" "}
            {trip.stops === 1 ? "stop" : "stops"}
          </p>
        </div>

        <div className="flex flex-col items-end gap-2">
          <StatusBadge status={trip.status} />
          <p className="text-sm text-text-muted">
            Planned budget{" "}
            <span className="font-semibold text-primary">
              {formatMoney(trip.budget)}
            </span>
          </p>
        </div>
      </div>

      <ItineraryBudgetView days={days} />
    </div>
  );
}
