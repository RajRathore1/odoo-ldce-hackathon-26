import { apiFetch } from "@/lib/api/session";
import { decodeText } from "@/lib/api/text";
import type { Paginated } from "@/lib/api/trips-service";
import type { Region } from "@/lib/types";

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

// Some cities come back with image_url set to an empty string.
function cityImage(dto: CityDto) {
  return dto.image_url || `https://picsum.photos/seed/city-${dto.id}/800/600`;
}

export function toRegion(dto: CityDto): Region {
  const state = decodeText(dto.state);
  const area = decodeText(dto.region);

  return {
    id: String(dto.id),
    name: decodeText(dto.name),
    country: decodeText(dto.country.name),
    blurb: [state, area].filter(Boolean).join(" - "),
    activityCount: dto.activities_count,
    avgDailyCost: Number(dto.avg_daily_cost) || 0,
    currency: dto.currency || "INR",
    image: cityImage(dto),
  };
}

export async function listCities(search?: string) {
  const query = new URLSearchParams({ page_size: "100" });
  if (search) query.set("search", search);

  const page = await apiFetch<Paginated<CityDto>>(`/cities/?${query}`);
  return page.results.map(toRegion);
}

export async function popularCities(limit = 8) {
  const cities = await apiFetch<CityDto[]>(`/cities/popular/?limit=${limit}`);
  return cities.map(toRegion);
}

export async function listCountries() {
  const page = await apiFetch<Paginated<CountryDto>>("/countries/?page_size=100");
  return page.results.map((country) => ({
    id: country.id,
    name: decodeText(country.name),
  }));
}
