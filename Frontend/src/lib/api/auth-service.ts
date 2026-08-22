import { apiUrl } from "@/lib/api/config";
import { readEnvelope } from "@/lib/api/envelope";
import type { AuthResult, RegisterPayload, Tokens } from "@/lib/api/types";


function post(path: string, body: unknown, accessToken?: string) {
  return fetch(apiUrl(path), {
    method: "POST",
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
    },
    body: JSON.stringify(body),
  });
}

export async function login(email: string, password: string) {
  return readEnvelope<AuthResult>(
    await post("/auth/login/", { email, password }),
  );
}

export async function register(payload: RegisterPayload) {
  return readEnvelope<AuthResult>(await post("/auth/register/", payload));
}

// Rotation is on: the response carries a new refresh token and the one we sent
// is blacklisted immediately. Store both or the next call signs the user out.
export async function refreshTokens(refresh: string) {
  return readEnvelope<Tokens>(
    await post("/auth/token/refresh/", { refresh }),
  );
}

export async function logout(refresh: string, accessToken?: string) {
  return readEnvelope<null>(
    await post("/auth/logout/", { refresh }, accessToken),
  );
}
