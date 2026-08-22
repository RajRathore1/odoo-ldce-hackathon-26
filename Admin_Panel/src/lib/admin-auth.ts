const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

const ACCESS_KEY = "gt-admin-access";
const REFRESH_KEY = "gt-admin-refresh";

type LoginResponse = {
  success: boolean;
  message: string | null;
  data: { tokens: { access: string; refresh: string } } | null;
};

export type AdminLoginResult = { ok: true } | { ok: false; message: string };

export async function adminLogin(
  email: string,
  password: string,
): Promise<AdminLoginResult> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/admin/auth/login/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
  } catch {
    return {
      ok: false,
      message: "Can't reach the server. Is the backend running?",
    };
  }

  const payload: LoginResponse | null = await response.json().catch(() => null);

  if (!response.ok || !payload?.success || !payload.data) {
    const fallback =
      response.status === 403
        ? "This account doesn't have admin access."
        : "Incorrect email or password.";
    return { ok: false, message: payload?.message ?? fallback };
  }

  window.sessionStorage.setItem(ACCESS_KEY, payload.data.tokens.access);
  window.sessionStorage.setItem(REFRESH_KEY, payload.data.tokens.refresh);
  return { ok: true };
}

export function isAdminAuthed() {
  if (typeof window === "undefined") return false;
  return Boolean(window.sessionStorage.getItem(ACCESS_KEY));
}

export function getAdminAccessToken() {
  if (typeof window === "undefined") return null;
  return window.sessionStorage.getItem(ACCESS_KEY);
}

export function clearAdminAuthed() {
  const refresh = window.sessionStorage.getItem(REFRESH_KEY);
  if (refresh) {
    fetch(`${API_BASE_URL}/auth/logout/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh }),
    }).catch(() => {});
  }
  window.sessionStorage.removeItem(ACCESS_KEY);
  window.sessionStorage.removeItem(REFRESH_KEY);
}
