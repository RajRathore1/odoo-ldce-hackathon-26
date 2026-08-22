import { nightsBetween } from "@/lib/format";
import type { SelectOption, Trip, TripStatus } from "@/lib/types";

export const statusFilters: SelectOption[] = [
  { label: "All trips", value: "all" },
  { label: "Ongoing", value: "ongoing" },
  { label: "Upcoming", value: "upcoming" },
  { label: "Completed", value: "completed" },
  { label: "Cancelled", value: "cancelled" },
];

export const groupOptions: SelectOption[] = [
  { label: "Nothing", value: "none" },
  { label: "Status", value: "status" },
  { label: "Country", value: "country" },
];

export const sortOptions: SelectOption[] = [
  { label: "Newest", value: "newest" },
  { label: "Budget", value: "budget" },
  { label: "Duration", value: "duration" },
  { label: "Name", value: "name" },
];

export function searchTrips(trips: Trip[], term: string) {
  const query = term.trim().toLowerCase();
  if (!query) return trips;

  return trips.filter((trip) =>
    [trip.title, trip.city, trip.country].some((field) =>
      field.toLowerCase().includes(query),
    ),
  );
}

export function filterByStatus(trips: Trip[], status: string) {
  if (status === "all") return trips;
  return trips.filter((trip) => trip.status === status);
}

export function sortTrips(trips: Trip[], order: string) {
  const sorted = [...trips];

  switch (order) {
    case "budget":
      return sorted.sort((a, b) => b.budget - a.budget);
    case "duration":
      return sorted.sort(
        (a, b) =>
          nightsBetween(b.startDate, b.endDate) -
          nightsBetween(a.startDate, a.endDate),
      );
    case "name":
      return sorted.sort((a, b) => a.title.localeCompare(b.title));
    default:
      return sorted.sort((a, b) => b.startDate.localeCompare(a.startDate));
  }
}

const statusLabels: Record<TripStatus, string> = {
  ongoing: "Ongoing",
  upcoming: "Upcoming",
  completed: "Completed",
  cancelled: "Cancelled",
};

export function groupTrips(trips: Trip[], key: string) {
  if (key === "none") return [{ label: "", trips }];

  const buckets = new Map<string, Trip[]>();

  for (const trip of trips) {
    const label = key === "status" ? statusLabels[trip.status] : trip.country;
    const bucket = buckets.get(label);
    if (bucket) {
      bucket.push(trip);
    } else {
      buckets.set(label, [trip]);
    }
  }

  return [...buckets].map(([label, items]) => ({ label, trips: items }));
}
