import { NextResponse, type NextRequest } from "next/server";
import { refreshTokens } from "@/lib/api/auth-service";
import {
  ACCESS_COOKIE,
  REFRESH_COOKIE,
  accessCookieOptions,
  refreshCookieOptions,
} from "@/lib/api/cookies";
import type { Tokens } from "@/lib/api/types";

const authPages = ["/login", "/register"];

// Refresh tokens rotate and the old one is blacklisted the moment it is spent,
// so two requests refreshing at once would sign the user out. Share one call
// per token, and hang on to the result briefly for requests that were already
// in flight with the previous cookie.
const inFlight = new Map<string, Promise<Tokens | null>>();

function refreshOnce(refresh: string) {
  const existing = inFlight.get(refresh);
  if (existing) return existing;

  const pending = refreshTokens(refresh)
    .catch(() => null)
    .finally(() => {
      setTimeout(() => inFlight.delete(refresh), 5000);
    });

  inFlight.set(refresh, pending);
  return pending;
}

function expiresWithin(token: string, ms: number) {
  const payload = token.split(".")[1];
  if (!payload) return true;

  try {
    const normalised = payload.replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalised.padEnd(
      normalised.length + ((4 - (normalised.length % 4)) % 4),
      "=",
    );
    const claims = JSON.parse(atob(padded)) as { exp?: number };
    if (typeof claims.exp !== "number") return true;
    return claims.exp * 1000 - Date.now() < ms;
  } catch {
    return true;
  }
}

function signInRedirect(request: NextRequest) {
  const url = new URL("/login", request.url);
  const target = request.nextUrl.pathname + request.nextUrl.search;
  if (target !== "/") url.searchParams.set("next", target);
  return NextResponse.redirect(url);
}

export async function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const onAuthPage = authPages.some((page) => pathname.startsWith(page));

  const access = request.cookies.get(ACCESS_COOKIE)?.value;
  const refresh = request.cookies.get(REFRESH_COOKIE)?.value;

  if (!refresh) {
    return onAuthPage ? NextResponse.next() : signInRedirect(request);
  }

  if (onAuthPage) {
    return NextResponse.redirect(new URL("/", request.url));
  }

  if (access && !expiresWithin(access, 60_000)) {
    return NextResponse.next();
  }

  const tokens = await refreshOnce(refresh);

  if (!tokens) {
    const response = signInRedirect(request);
    response.cookies.delete(ACCESS_COOKIE);
    response.cookies.delete(REFRESH_COOKIE);
    return response;
  }

  // Update the request too, so the page being rendered sees the new token
  // rather than the stale one it arrived with.
  request.cookies.set(ACCESS_COOKIE, tokens.access);
  request.cookies.set(REFRESH_COOKIE, tokens.refresh);

  const response = NextResponse.next({ request: { headers: request.headers } });
  response.cookies.set(ACCESS_COOKIE, tokens.access, accessCookieOptions());
  response.cookies.set(REFRESH_COOKIE, tokens.refresh, refreshCookieOptions());
  return response;
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
