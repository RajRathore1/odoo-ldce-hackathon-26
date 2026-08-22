import { notFound } from "next/navigation";
import { ItineraryBudgetView } from "@/components/itinerary-budget-view";
import { StatusBadge } from "@/components/ui/badge";
import { TripBudgetPanel } from "@/components/trip-budget-panel";
import { getBudget, listExpenses } from "@/lib/api/budget-service";
import { ApiError } from "@/lib/api/envelope";
import {
  getItinerary,
  getTripDto,
  listStops,
  toTrip,
} from "@/lib/api/trips-service";
import { formatDateRange, formatMoney } from "@/lib/format";

export default async function TripItineraryPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  let trip;
  let days;
  let budget;
  let expenses;
  let stops;
  let tripDates = { start: "", end: "" };

  try {
    const [dto, itinerary, budgetDto, expenseRows, stopRows] =
      await Promise.all([
        getTripDto(id),
        getItinerary(id),
        getBudget(id),
        listExpenses(id),
        listStops(id),
      ]);
    trip = toTrip(dto);
    days = itinerary;
    budget = budgetDto;
    expenses = expenseRows;
    stops = stopRows;
    tripDates = { start: dto.start_date, end: dto.end_date };
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

      <TripBudgetPanel
        tripId={id}
        budget={budget}
        expenses={expenses}
        stops={stops.map((stop) => ({
          label: stop.title || stop.city.name,
          value: String(stop.id),
        }))}
        tripStart={tripDates.start}
        tripEnd={tripDates.end}
      />
    </div>
  );
}
