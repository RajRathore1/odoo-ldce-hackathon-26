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
