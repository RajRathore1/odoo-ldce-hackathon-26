export type CountryDto = {
  id: number;
  name: string;
  iso2: string;
  region: string;
  currency_code: string;
};

export type CityDto = {
  id: number;
  name: string;
  state: string;
  country: { id: number; name: string; iso2: string };
  region: string;
  cost_index: string;
  avg_daily_cost: string;
  currency: string;
  popularity_score: number;
  image_url: string;
  activities_count: number;
  is_saved: boolean;
};

export type CityActivity = {
  id: number;
  name: string;
  activity_type: string;
  cost: string;
  currency: string;
  duration_minutes: number | null;
  rating: string | null;
  image_url: string;
};

export type CityDetailDto = CityDto & {
  description: string;
  timezone: string;
  top_activities: CityActivity[];
};

export type SavedDestinationDto = {
  id: number;
  city: { id: number; name: string; country_name: string };
  note: string;
};
