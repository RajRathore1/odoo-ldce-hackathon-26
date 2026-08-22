// Names and options only, no next/headers - proxy.ts imports this too.

export const ACCESS_COOKIE = "gt_access";
export const REFRESH_COOKIE = "gt_refresh";

const ACCESS_MAX_AGE = 60 * 60; // access tokens live an hour
const REFRESH_MAX_AGE = 60 * 60 * 24 * 7; // refresh tokens live a week

function base() {
  return {
    httpOnly: true,
    sameSite: "lax" as const,
    secure: process.env.NODE_ENV === "production",
    path: "/",
  };
}

export function accessCookieOptions() {
  return { ...base(), maxAge: ACCESS_MAX_AGE };
}

export function refreshCookieOptions() {
  return { ...base(), maxAge: REFRESH_MAX_AGE };
}
