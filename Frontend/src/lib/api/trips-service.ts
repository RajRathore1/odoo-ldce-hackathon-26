export type Paginated<T> = {
  results: T[];
  pagination: { count: number; page: number; pages: number };
};

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

export type CreateTripPayload = {
  name: string;
  start_date: string;
  end_date: string;
  description?: string;
  total_budget?: string;
  currency?: string;
};

export type StopDto = {
  id: number;
  title: string;
  city: { id: number; name: string; country_name: string };
  start_date: string;
  end_date: string;
  nights: number;
  order: number;
  budget: string | null;
  activities_count: number;
  notes: string;
};
