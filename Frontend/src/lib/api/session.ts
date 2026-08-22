import { cookies } from "next/headers";
import { apiUrl } from "@/lib/api/config";
import {
  ACCESS_COOKIE,
  REFRESH_COOKIE,
  accessCookieOptions,
  refreshCookieOptions,
} from "@/lib/api/cookies";
import { ApiError, readEnvelope } from "@/lib/api/envelope";
import type { AuthUser, Tokens } from "@/lib/api/types";

export async function setSession(tokens: Tokens) {
  const store = await cookies();
  store.set(ACCESS_COOKIE, tokens.access, accessCookieOptions());
  store.set(REFRESH_COOKIE, tokens.refresh, refreshCookieOptions());
}

export async function clearSession() {
  const store = await cookies();
  store.delete(ACCESS_COOKIE);
  store.delete(REFRESH_COOKIE);
}

export async function readTokens() {
  const store = await cookies();
  return {
    access: store.get(ACCESS_COOKIE)?.value,
    refresh: store.get(REFRESH_COOKIE)?.value,
  };
}

/**
 * Authenticated call for server components and route handlers.
 *
 * There is deliberately no refresh-and-retry here: proxy.ts rotates the access
 * token before the request reaches this point, and a server component cannot
 * write the replacement cookie anyway.
 */
export async function apiFetch<T>(path: string, init: RequestInit = {}) {
  const { access } = await readTokens();

  const response = await fetch(apiUrl(path), {
    ...init,
    cache: "no-store",
    headers: {
      Accept: "application/json",
      ...(init.body ? { "Content-Type": "application/json" } : {}),
      ...(access ? { Authorization: `Bearer ${access}` } : {}),
      ...init.headers,
    },
  });

  return readEnvelope<T>(response);
}

export async function getCurrentUser() {
  const { access } = await readTokens();
  if (!access) return null;

  try {
    return await apiFetch<AuthUser>("/users/me/");
  } catch (error) {
    // A signed-out or half-expired session should render the page, not crash it.
    if (error instanceof ApiError && error.status === 401) return null;
    throw error;
  }
}
