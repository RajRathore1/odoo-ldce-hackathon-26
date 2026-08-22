const ACCESS_KEY = "gt_access";
const REFRESH_KEY = "gt_refresh";

export type Tokens = { access: string; refresh: string };

export function readTokens(): Partial<Tokens> {
  if (typeof window === "undefined") return {};

  return {
    access: window.localStorage.getItem(ACCESS_KEY) ?? undefined,
    refresh: window.localStorage.getItem(REFRESH_KEY) ?? undefined,
  };
}

export function storeTokens(tokens: Tokens) {
  window.localStorage.setItem(ACCESS_KEY, tokens.access);
  window.localStorage.setItem(REFRESH_KEY, tokens.refresh);
}

export function clearTokens() {
  window.localStorage.removeItem(ACCESS_KEY);
  window.localStorage.removeItem(REFRESH_KEY);
}

export function hasSession() {
  return Boolean(readTokens().refresh);
}
