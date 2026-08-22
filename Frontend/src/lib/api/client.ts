import { ApiError, readEnvelope } from "@/lib/api/envelope";
import {
  clearTokens,
  readTokens,
  storeTokens,
  type Tokens,
} from "@/lib/api/tokens";

const root = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

export function apiUrl(path: string) {
  return `${root.replace(/\/+$/, "")}/api/v1${path}`;
}

type Options = Omit<RequestInit, "body"> & {
  body?: unknown;
  /** Skip the bearer token, for login and register. */
  anonymous?: boolean;
};

async function send<T>(path: string, options: Options, accessToken?: string) {
  const { body, anonymous, headers, ...rest } = options;

  const response = await fetch(apiUrl(path), {
    ...rest,
    headers: {
      Accept: "application/json",
      ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
      ...(!anonymous && accessToken
        ? { Authorization: `Bearer ${accessToken}` }
        : {}),
      ...headers,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  return readEnvelope<T>(response);
}

// Refresh tokens rotate and the spent one is blacklisted immediately, so two
// requests refreshing at once would sign the user out. Everyone waits on the
// same call.
let refreshing: Promise<Tokens | null> | null = null;

function refreshOnce() {
  if (refreshing) return refreshing;

  const { refresh } = readTokens();
  if (!refresh) return Promise.resolve(null);

  refreshing = send<Tokens>(
    "/auth/token/refresh/",
    { method: "POST", body: { refresh }, anonymous: true },
  )
    .then((tokens) => {
      storeTokens(tokens);
      return tokens;
    })
    .catch(() => null)
    .finally(() => {
      refreshing = null;
    });

  return refreshing;
}

const SIGNED_OUT = "globetrotter:signed-out";

// The client cannot route on its own, so it announces the dead session and the
// auth provider does the redirect.
export function onSignedOut(handler: () => void) {
  window.addEventListener(SIGNED_OUT, handler);
  return () => window.removeEventListener(SIGNED_OUT, handler);
}

function abandonSession() {
  clearTokens();
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event(SIGNED_OUT));
  }
}

export async function api<T>(path: string, options: Options = {}): Promise<T> {
  const { access } = readTokens();

  try {
    return await send<T>(path, options, access);
  } catch (error) {
    const unauthorised = error instanceof ApiError && error.status === 401;
    if (!unauthorised || options.anonymous) throw error;

    const tokens = await refreshOnce();
    if (!tokens) {
      abandonSession();
      throw error;
    }

    try {
      return await send<T>(path, options, tokens.access);
    } catch (retryError) {
      if (retryError instanceof ApiError && retryError.status === 401) {
        abandonSession();
      }
      throw retryError;
    }
  }
}
