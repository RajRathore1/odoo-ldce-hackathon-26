import { apiUrl } from "@/lib/api/config";
import { readEnvelope } from "@/lib/api/envelope";
import { failure } from "@/lib/api/route-helpers";
import { apiFetchWithRefresh, readTokens } from "@/lib/api/session";
import type { AuthUser } from "@/lib/api/types";

export async function PATCH(request: Request) {
  const payload = await request.json();

  try {
    const user = await apiFetchWithRefresh<AuthUser>("/users/me/", {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
    return Response.json({ user });
  } catch (error) {
    return failure(error);
  }
}

// Avatar is multipart, so it bypasses the JSON helper and streams the form
// straight through with the access token attached.
export async function POST(request: Request) {
  const form = await request.formData();
  const { access } = await readTokens();

  try {
    const response = await fetch(apiUrl("/users/me/avatar/"), {
      method: "POST",
      cache: "no-store",
      headers: access ? { Authorization: `Bearer ${access}` } : {},
      body: form,
    });
    const user = await readEnvelope<AuthUser>(response);
    return Response.json({ user });
  } catch (error) {
    return failure(error);
  }
}
