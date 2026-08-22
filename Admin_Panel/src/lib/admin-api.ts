import { clearAdminAuthed, getAdminAccessToken } from "@/lib/admin-auth";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export type AdminApiUser = {
  id: number;
  email: string;
  full_name: string;
  role: "USER" | "ADMIN";
  is_active: boolean;
  is_staff: boolean;
  is_deleted: boolean;
  city_name: string | null;
  country_name: string | null;
  trips_count: number;
  posts_count: number;
  last_login: string | null;
  created_at: string;
};

export type AdminApiCity = {
  id: number;
  name: string;
  country_name: string;
  popularity_score: number;
  is_active: boolean;
};

export type AdminApiActivity = {
  id: number;
  name: string;
  city_name: string;
  category_name: string;
  activity_type: string;
  popularity_score: number;
  is_active: boolean;
};

export type AdminApiTrip = {
  id: number;
  name: string;
  user_email: string;
  status: "DRAFT" | "PLANNED" | "ONGOING" | "COMPLETED" | "CANCELLED";
  start_date: string;
  end_date: string;
  duration_days: number;
  total_budget: string | null;
  estimated_cost: string;
  currency: string;
  is_deleted: boolean;
  created_at: string;
};

async function adminFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getAdminAccessToken();

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init?.headers,
    },
  });

  if (response.status === 401) {
    clearAdminAuthed();
    window.location.href = "/login";
    throw new Error("Session expired");
  }

  if (response.status === 204) {
    return null as T;
  }

  const payload = await response.json().catch(() => null);

  if (!response.ok || !payload?.success) {
    throw new Error(payload?.message ?? "Request failed");
  }

  return payload.data as T;
}

export function fetchAdminUsers(search?: string) {
  const query = new URLSearchParams({ page_size: "100" });
  if (search) query.set("search", search);
  return adminFetch<{ results: AdminApiUser[] }>(
    `/admin/users/?${query.toString()}`,
  );
}

export function updateAdminUserActive(id: number, isActive: boolean) {
  return adminFetch<AdminApiUser>(`/admin/users/${id}/`, {
    method: "PATCH",
    body: JSON.stringify({ is_active: isActive }),
  });
}

export function fetchAdminCities(limit = 6) {
  const query = new URLSearchParams({
    page_size: String(limit),
    ordering: "-popularity_score",
  });
  return adminFetch<{ results: AdminApiCity[] }>(
    `/admin/cities/?${query.toString()}`,
  );
}

export function fetchAdminActivities(limit = 30) {
  const query = new URLSearchParams({
    page_size: String(limit),
    ordering: "-popularity_score",
  });
  return adminFetch<{ results: AdminApiActivity[] }>(
    `/admin/activities/?${query.toString()}`,
  );
}

export function fetchAdminTrips(search?: string) {
  const query = new URLSearchParams({ page_size: "100" });
  if (search) query.set("search", search);
  return adminFetch<{ results: AdminApiTrip[] }>(
    `/admin/trips/?${query.toString()}`,
  );
}

export function deleteAdminTrip(id: number) {
  return adminFetch<null>(`/admin/trips/${id}/`, { method: "DELETE" });
}
