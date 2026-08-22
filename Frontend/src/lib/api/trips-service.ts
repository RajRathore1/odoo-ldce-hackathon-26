import { apiFetch } from "@/lib/api/session";
import type { ItineraryDay, Trip, TripStatus } from "@/lib/types";

export type TripDto = {
  id: number;
  name: string;
  description: string;
  start_date: string;
  end_date: string;
  duration_days: number;
  status: "DRAFT" | "PLANNED" | "ONGOING" | "COMPLETED" | "CANCELLED";
  cover_photo: string | null;
  stops_count: number;
  activities_count: number;
  cities: string[];
  total_budget: string | null;
  estimated_cost: string;
  currency: string;
  is_over_budget: boolean;
  is_public: boolean;
  created_at: string;
};

export type Paginated<T> = {
  results: T[];
  pagination: { count: number; page: number; pages: number };
};

export type CreateTripPayload = {
  name: string;
  start_date: string;
  end_date: string;
  description?: string;
  total_budget?: string;
  currency?: string;
};

const statusMap: Record<TripDto["status"], TripStatus> = {
  DRAFT: "upcoming",
  PLANNED: "upcoming",
  ONGOING: "ongoing",
  COMPLETED: "completed",
  CANCELLED: "cancelled",
};

// Trips have no cover photo until someone uploads one. Pick a stable stand-in
// per trip so the grid does not look half-finished.
const fallbackCovers = [
  "https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?fm=jpg&q=70&w=800&auto=format&fit=crop",
  "https://images.unsplash.com/photo-1501785888041-af3ef285b470?fm=jpg&q=70&w=800&auto=format&fit=crop",
  "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?fm=jpg&q=70&w=800&auto=format&fit=crop",
  "https://images.unsplash.com/photo-1519681393784-d120267933ba?fm=jpg&q=70&w=800&auto=format&fit=crop",
];

export function toTrip(dto: TripDto): Trip {
  const budget = dto.total_budget ?? dto.estimated_cost;

  return {
    id: String(dto.id),
    title: dto.name,
    city: dto.cities[0] ?? "",
    country: dto.cities.length > 1 ? `+${dto.cities.length - 1} more` : "",
    startDate: dto.start_date,
    endDate: dto.end_date,
    budget: Number(budget) || 0,
    stops: dto.stops_count,
    status: statusMap[dto.status] ?? "upcoming",
    image: dto.cover_photo ?? fallbackCovers[dto.id % fallbackCovers.length],
  };
}

export async function listTrips() {
  const page = await apiFetch<Paginated<TripDto>>("/trips/?page_size=100");
  return page.results.map(toTrip);
}

export function getTripDto(id: string) {
  return apiFetch<TripDto>(`/trips/${id}/`);
}

export type ItineraryDto = {
  trip: { id: number; name: string; currency: string };
  days: {
    date: string;
    day_number: number;
    stop: { id: number; title: string } | null;
    activities: { id: number; title: string; cost: string }[];
    day_total_cost: string;
  }[];
  totals: { grand_total: string };
};

export async function getItinerary(id: string) {
  const dto = await apiFetch<ItineraryDto>(`/trips/${id}/itinerary/`);

  return dto.days.map<ItineraryDay>((day) => ({
    day: day.day_number,
    activities: day.activities.map((activity) => ({
      id: String(activity.id),
      activity: activity.title,
      expense: Number(activity.cost) || 0,
    })),
  }));
}
