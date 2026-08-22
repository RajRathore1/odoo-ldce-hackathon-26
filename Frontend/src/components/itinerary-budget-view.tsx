"use client";

import { useMemo, useState } from "react";
import { SearchFilterBar } from "@/components/search-filter-bar";
import { formatMoney } from "@/lib/format";
import type { ItineraryDay, SelectOption } from "@/lib/types";

const sortOptions: SelectOption[] = [
  { label: "Day order", value: "day" },
  { label: "Highest expense", value: "expense-desc" },
];

export function ItineraryBudgetView({ days }: { days: ItineraryDay[] }) {
  const [search, setSearch] = useState("");
  const [order, setOrder] = useState("day");

  const filteredDays = useMemo(() => {
    const query = search.trim().toLowerCase();
    return days
      .map((day) => ({
        ...day,
        activities: query
          ? day.activities.filter((activity) =>
              activity.activity.toLowerCase().includes(query),
            )
          : day.activities,
      }))
      .filter((day) => day.activities.length > 0);
  }, [days, search]);

  const orderedDays = useMemo(() => {
    if (order !== "expense-desc") return filteredDays;
    return filteredDays.map((day) => ({
      ...day,
      activities: [...day.activities].sort((a, b) => b.expense - a.expense),
    }));
  }, [filteredDays, order]);

  const dayTotals = orderedDays.map((day) =>
    day.activities.reduce((sum, activity) => sum + activity.expense, 0),
  );
  const runningTotals = dayTotals.reduce<number[]>((acc, total, index) => {
    acc.push((acc[index - 1] ?? 0) + total);
    return acc;
  }, []);

  const searching = search.trim().length > 0;

  return (
    <div className="space-y-6">
      <SearchFilterBar
        search={search}
        onSearchChange={setSearch}
        placeholder="Search an activity"
        sortBy={{ value: order, onChange: setOrder, options: sortOptions }}
      />

      {orderedDays.length > 0 ? (
        <div className="space-y-5">
          {orderedDays.map((day, index) => (
            <DayCard
              key={day.day}
              day={day}
              dayTotal={dayTotals[index]}
              runningTotal={runningTotals[index]}
            />
          ))}

          <div className="flex items-center justify-between rounded-2xl border border-border bg-surface p-5 shadow-sm sm:p-6">
            <span className="font-medium text-text-muted">
              Total across {orderedDays.length}{" "}
              {orderedDays.length === 1 ? "day" : "days"}
            </span>
            <span className="font-heading text-xl font-semibold text-primary">
              {formatMoney(runningTotals[runningTotals.length - 1] ?? 0)}
            </span>
          </div>
        </div>
      ) : (
        <p className="rounded-2xl border border-dashed border-border px-6 py-12 text-center text-sm text-text-muted">
          {searching
            ? `No activities match "${search.trim()}".`
            : "No itinerary added for this trip yet."}
        </p>
      )}
    </div>
  );
}

function DayCard({
  day,
  dayTotal,
  runningTotal,
}: {
  day: ItineraryDay;
  dayTotal: number;
  runningTotal: number;
}) {
  return (
    <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm transition-shadow hover:shadow-md sm:p-6">
      <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
        <h3 className="inline-flex items-center gap-2 font-heading text-lg font-semibold">
          <span className="flex size-7 items-center justify-center rounded-full bg-primary text-sm text-white">
            {day.day}
          </span>
          Day {day.day}
        </h3>
        <p className="text-sm text-text-muted">
          Day total{" "}
          <span className="font-semibold text-text">
            {formatMoney(dayTotal)}
          </span>
          <span className="mx-2 text-border">|</span>
          Running total{" "}
          <span className="font-semibold text-primary">
            {formatMoney(runningTotal)}
          </span>
        </p>
      </div>

      <ul className="divide-y divide-border">
        {day.activities.map((activity) => (
          <li
            key={activity.id}
            className="flex items-center justify-between gap-4 py-2.5 text-sm"
          >
            <span>{activity.activity}</span>
            <span className="font-medium text-text-muted">
              {formatMoney(activity.expense)}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
