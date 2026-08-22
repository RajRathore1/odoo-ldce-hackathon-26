"use client";

import { use } from "react";
import { ItineraryBudgetView } from "@/components/itinerary-budget-view";
import { ErrorBlock, LoadingBlock } from "@/components/page-state";
import { TripBudgetPanel } from "@/components/trip-budget-panel";
import { StatusBadge } from "@/components/ui/badge";
import { toItineraryDays, toTrip, type ItineraryDto } from "@/lib/api/adapters";
import type { BudgetDto, ExpenseDto } from "@/lib/api/budget-types";
import type { Paginated, StopDto, TripDto } from "@/lib/api/trips-service";
import { useApi } from "@/lib/api/use-api";
import { formatDateRange, formatMoney } from "@/lib/format";

export default function TripPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);

  const trip = useApi<TripDto>(`/trips/${id}/`);
  const itinerary = useApi<ItineraryDto>(`/trips/${id}/itinerary/`);
  const budget = useApi<BudgetDto>(`/trips/${id}/budget/`);
  const expenses = useApi<Paginated<ExpenseDto>>(
    `/trips/${id}/expenses/?page_size=100`,
  );
  const stops = useApi<Paginated<StopDto>>(`/trips/${id}/stops/?page_size=100`);

  function refreshAfterChange() {
    budget.reload();
    expenses.reload();
    itinerary.reload();
  }

  if (trip.loading) return <LoadingBlock label="Loading trip" />;
  if (trip.error) {
    return <ErrorBlock message={trip.error} onRetry={trip.reload} />;
  }
  if (!trip.data) return null;

  const dto = trip.data;
  const view = toTrip(dto);
  const place = [view.city, view.country].filter(Boolean).join(", ");

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          {place && (
            <p className="text-sm font-medium text-text-muted">{place}</p>
          )}
          <h1 className="mt-1 font-heading text-3xl font-semibold sm:text-4xl">
            {view.title}
          </h1>
          <p className="mt-2 text-text-muted">
            {formatDateRange(view.startDate, view.endDate)} · {view.stops}{" "}
            {view.stops === 1 ? "stop" : "stops"}
          </p>
        </div>

        <div className="flex flex-col items-end gap-2">
          <StatusBadge status={view.status} />
          <p className="text-sm text-text-muted">
            Planned budget{" "}
            <span className="font-semibold text-primary">
              {formatMoney(view.budget, dto.currency)}
            </span>
          </p>
        </div>
      </div>

      {itinerary.data && (
        <ItineraryBudgetView days={toItineraryDays(itinerary.data)} />
      )}

      {budget.data && (
        <TripBudgetPanel
          tripId={id}
          budget={budget.data}
          expenses={expenses.data?.results ?? []}
          stops={(stops.data?.results ?? []).map((stop) => ({
            label: stop.title || stop.city.name,
            value: String(stop.id),
          }))}
          tripStart={dto.start_date}
          tripEnd={dto.end_date}
          onChanged={refreshAfterChange}
        />
      )}
    </div>
  );
}
