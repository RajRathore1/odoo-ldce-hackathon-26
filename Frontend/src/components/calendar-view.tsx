"use client";

import { useMemo, useState } from "react";
import { cn } from "@/lib/cn";
import { SearchFilterBar } from "@/components/search-filter-bar";
import { SectionHeader } from "@/components/section-header";
import { TripCard } from "@/components/trip-card";
import { trips } from "@/lib/mock-data";
import type { Trip, TripStatus } from "@/lib/types";

const monthNames = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];
const weekdayLabels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

const statusDot: Record<TripStatus, string> = {
  ongoing: "bg-warning",
  upcoming: "bg-info",
  completed: "bg-success",
};

// Trip dates are plain YYYY-MM-DD calendar dates, so every date computed here
// stays in UTC — mixing in local-time Date methods would shift keys by a day.
function pad(value: number) {
  return String(value).padStart(2, "0");
}

function dateKey(year: number, month: number, day: number) {
  return `${year}-${pad(month + 1)}-${pad(day)}`;
}

function eachDateKeyInRange(start: string, end: string) {
  const keys: string[] = [];
  const cursor = new Date(`${start}T00:00:00Z`);
  const last = new Date(`${end}T00:00:00Z`);
  while (cursor.getTime() <= last.getTime()) {
    keys.push(cursor.toISOString().slice(0, 10));
    cursor.setUTCDate(cursor.getUTCDate() + 1);
  }
  return keys;
}

export function CalendarView() {
  const [cursor, setCursor] = useState(() => {
    const now = new Date();
    return { year: now.getUTCFullYear(), month: now.getUTCMonth() };
  });
  const [search, setSearch] = useState("");

  const now = new Date();
  const todayKey = dateKey(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate());

  const visibleTrips = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return trips;
    return trips.filter((trip) =>
      [trip.title, trip.city, trip.country].some((field) =>
        field.toLowerCase().includes(query),
      ),
    );
  }, [search]);

  const tripsByDate = useMemo(() => {
    const map = new Map<string, Trip[]>();
    for (const trip of visibleTrips) {
      for (const key of eachDateKeyInRange(trip.startDate, trip.endDate)) {
        const bucket = map.get(key);
        if (bucket) bucket.push(trip);
        else map.set(key, [trip]);
      }
    }
    return map;
  }, [visibleTrips]);

  const weeks = useMemo(() => {
    const firstWeekday = new Date(
      Date.UTC(cursor.year, cursor.month, 1),
    ).getUTCDay();
    const daysInMonth = new Date(
      Date.UTC(cursor.year, cursor.month + 1, 0),
    ).getUTCDate();

    const cells: ({ day: number; key: string } | null)[] = [];
    for (let i = 0; i < firstWeekday; i++) cells.push(null);
    for (let day = 1; day <= daysInMonth; day++) {
      cells.push({ day, key: dateKey(cursor.year, cursor.month, day) });
    }
    while (cells.length % 7 !== 0) cells.push(null);

    const rows: ({ day: number; key: string } | null)[][] = [];
    for (let i = 0; i < cells.length; i += 7) rows.push(cells.slice(i, i + 7));
    return rows;
  }, [cursor]);

  const monthTrips = useMemo(() => {
    const daysInMonth = new Date(
      Date.UTC(cursor.year, cursor.month + 1, 0),
    ).getUTCDate();
    const monthStartKey = dateKey(cursor.year, cursor.month, 1);
    const monthEndKey = dateKey(cursor.year, cursor.month, daysInMonth);
    return visibleTrips.filter(
      (trip) => trip.startDate <= monthEndKey && trip.endDate >= monthStartKey,
    );
  }, [visibleTrips, cursor]);

  function shiftMonth(delta: number) {
    setCursor((current) => {
      const total = current.year * 12 + current.month + delta;
      return { year: Math.floor(total / 12), month: ((total % 12) + 12) % 12 };
    });
  }

  return (
    <div className="space-y-6">
      <SearchFilterBar
        search={search}
        onSearchChange={setSearch}
        placeholder="Search a trip, city or country"
      />

      <div className="rounded-2xl border border-border bg-surface p-4 shadow-sm sm:p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-heading text-lg font-semibold sm:text-xl">
            {monthNames[cursor.month]} {cursor.year}
          </h2>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => shiftMonth(-1)}
              aria-label="Previous month"
              className="rounded-lg border border-border p-1.5 text-text-muted transition-colors hover:bg-bg"
            >
              <ChevronIcon direction="left" />
            </button>
            <button
              type="button"
              onClick={() => shiftMonth(1)}
              aria-label="Next month"
              className="rounded-lg border border-border p-1.5 text-text-muted transition-colors hover:bg-bg"
            >
              <ChevronIcon direction="right" />
            </button>
          </div>
        </div>

        <div className="grid grid-cols-7 gap-1 text-center text-xs font-medium text-text-muted">
          {weekdayLabels.map((label) => (
            <div key={label} className="py-1">
              {label}
            </div>
          ))}
        </div>

        <div className="space-y-1">
          {weeks.map((week, weekIndex) => (
            <div key={weekIndex} className="grid grid-cols-7 gap-1">
              {week.map((cell, cellIndex) => {
                if (!cell) {
                  return (
                    <div key={cellIndex} className="aspect-square" />
                  );
                }

                const dayTrips = tripsByDate.get(cell.key) ?? [];
                const isToday = cell.key === todayKey;

                return (
                  <div
                    key={cell.key}
                    className={cn(
                      "flex aspect-square flex-col gap-1 rounded-lg border p-1.5 text-left",
                      isToday ? "border-primary bg-primary/5" : "border-transparent",
                    )}
                  >
                    <span
                      className={cn(
                        "text-xs font-medium",
                        isToday ? "text-primary" : "text-text",
                      )}
                    >
                      {cell.day}
                    </span>
                    <div className="flex flex-wrap gap-1">
                      {dayTrips.slice(0, 3).map((trip) => (
                        <span
                          key={trip.id}
                          title={trip.title}
                          className={cn("size-1.5 rounded-full", statusDot[trip.status])}
                        />
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>

      <div className="flex flex-wrap gap-4 text-sm text-text-muted">
        <span className="inline-flex items-center gap-1.5">
          <span className="size-1.5 rounded-full bg-warning" /> Ongoing
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="size-1.5 rounded-full bg-info" /> Up-coming
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="size-1.5 rounded-full bg-success" /> Completed
        </span>
      </div>

      <section>
        <SectionHeader title={`Trips in ${monthNames[cursor.month]} ${cursor.year}`} />
        {monthTrips.length > 0 ? (
          <div className="grid grid-cols-[repeat(auto-fit,minmax(260px,1fr))] gap-4">
            {monthTrips.map((trip) => (
              <TripCard key={trip.id} trip={trip} href={`/trips/${trip.id}`} />
            ))}
          </div>
        ) : (
          <p className="rounded-2xl border border-dashed border-border px-6 py-10 text-center text-sm text-text-muted">
            No trips fall in this month.
          </p>
        )}
      </section>
    </div>
  );
}

function ChevronIcon({ direction }: { direction: "left" | "right" }) {
  return (
    <svg
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="size-4"
      aria-hidden
    >
      <path d={direction === "left" ? "M10 3 5 8l5 5" : "M6 3l5 5-5 5"} />
    </svg>
  );
}
