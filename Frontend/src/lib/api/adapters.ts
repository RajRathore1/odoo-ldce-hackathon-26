import type { CityDto } from "@/lib/api/geo-service";
import type { TripDto } from "@/lib/api/trips-service";
import type { ItineraryDay, Region, Trip, TripStatus } from "@/lib/types";

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
  return {
    id: String(dto.id),
    title: dto.name,
    city: dto.cities[0] ?? "",
    country: dto.cities.length > 1 ? `+${dto.cities.length - 1} more` : "",
    startDate: dto.start_date,
    endDate: dto.end_date,
    budget: Number(dto.total_budget ?? dto.estimated_cost) || 0,
    stops: dto.stops_count,
    status: statusMap[dto.status] ?? "upcoming",
    image: dto.cover_photo ?? fallbackCovers[dto.id % fallbackCovers.length],
  };
}

// Some cities come back with image_url set to an empty string.
export function cityImage(id: number, url: string) {
  return url || `https://picsum.photos/seed/city-${id}/800/600`;
}

export function toRegion(dto: CityDto): Region {
  return {
    id: String(dto.id),
    name: dto.name,
    country: dto.country.name,
    blurb: [dto.state, dto.region].filter(Boolean).join(" - "),
    activityCount: dto.activities_count,
    avgDailyCost: Number(dto.avg_daily_cost) || 0,
    currency: dto.currency || "INR",
    image: cityImage(dto.id, dto.image_url),
  };
}

export type ItineraryDto = {
  days: {
    date: string;
    day_number: number;
    activities: { id: number; title: string; cost: string }[];
  }[];
};

export function toItineraryDays(dto: ItineraryDto): ItineraryDay[] {
  return dto.days.map((day) => ({
    day: day.day_number,
    activities: day.activities.map((activity) => ({
      id: String(activity.id),
      activity: activity.title,
      expense: Number(activity.cost) || 0,
    })),
  }));
}
