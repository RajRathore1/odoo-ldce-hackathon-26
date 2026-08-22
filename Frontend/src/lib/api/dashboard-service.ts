import { apiFetch } from "@/lib/api/session";

export type DashboardDto = {
  user: { first_name: string; avatar: string | null };
  counts: {
    total_trips: number;
    ongoing: number;
    upcoming: number;
    completed: number;
  };
  ongoing_trip: {
    id: number;
    name: string;
    start_date: string;
    end_date: string;
    stops_count: number;
    days_remaining: number;
    cover_photo: string | null;
  } | null;
  recent_trips: {
    id: number;
    name: string;
    status: string;
    start_date: string;
    end_date: string;
    stops_count: number;
    estimated_cost: string;
    currency: string;
    cover_photo: string | null;
  }[];
  popular_cities: {
    id: number;
    name: string;
    country_name: string;
    popularity_score: number;
    image_url: string;
  }[];
  budget_highlights: {
    currency: string;
    total_planned: string;
    upcoming_trips_budget: string;
    avg_cost_per_trip: string;
    over_budget_trips: number;
  };
};

export function getDashboard() {
  return apiFetch<DashboardDto>("/dashboard/");
}
