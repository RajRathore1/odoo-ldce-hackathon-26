const ACCESS_KEY = "gt_access";
const REFRESH_KEY = "gt_refresh";

const ACCESS_MAX_AGE = 60 * 60; // access tokens last an hour
const REFRESH_MAX_AGE = 60 * 60 * 24 * 7; // refresh tokens last a week

export type Tokens = { access: string; refresh: string };

function readCookie(name: string) {
  if (typeof document === "undefined") return undefined;

  const prefix = `${name}=`;
  // Separator is ";" plus optional whitespace, not always "; ".
  for (const part of document.cookie.split(/;\s*/)) {
    if (part.startsWith(prefix)) {
      return decodeURIComponent(part.slice(prefix.length)) || undefined;
    }
  }

  return undefined;
}

function writeCookie(name: string, value: string, maxAge: number) {
  if (typeof document === "undefined") return;

  // Not httpOnly on purpose: the browser calls the API directly, so it has to
  // read the token back to build the Authorization header.
  const attributes = [
    `${name}=${encodeURIComponent(value)}`,
    "path=/",
    `max-age=${maxAge}`,
    "samesite=lax",
  ];

  if (window.location.protocol === "https:") attributes.push("secure");

  document.cookie = attributes.join("; ");
}

function deleteCookie(name: string) {
  if (typeof document === "undefined") return;
  document.cookie = `${name}=; path=/; max-age=0; samesite=lax`;
}

export function readTokens(): Partial<Tokens> {
  return {
    access: readCookie(ACCESS_KEY),
    refresh: readCookie(REFRESH_KEY),
  };
}

export function storeTokens(tokens: Tokens) {
  writeCookie(ACCESS_KEY, tokens.access, ACCESS_MAX_AGE);
  writeCookie(REFRESH_KEY, tokens.refresh, REFRESH_MAX_AGE);
}

export function clearTokens() {
  deleteCookie(ACCESS_KEY);
  deleteCookie(REFRESH_KEY);
}

export function hasSession() {
  return Boolean(readTokens().refresh);
}
