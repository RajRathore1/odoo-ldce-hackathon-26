import { logout } from "@/lib/api/auth-service";
import { clearSession, readTokens } from "@/lib/api/session";

export async function POST() {
  const { access, refresh } = await readTokens();

  if (refresh) {
    // Best effort: the cookies go regardless, so a backend hiccup can never
    // leave someone stuck in a session they asked to end.
    try {
      await logout(refresh, access);
    } catch (error) {
      console.error("Backend logout failed", error);
    }
  }

  await clearSession();
  return Response.json({ ok: true });
}
