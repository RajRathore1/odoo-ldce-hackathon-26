import { register } from "@/lib/api/auth-service";
import { failure } from "@/lib/api/route-helpers";
import { setSession } from "@/lib/api/session";
import type { RegisterPayload } from "@/lib/api/types";

export async function POST(request: Request) {
  const payload = (await request.json()) as RegisterPayload;

  try {
    const { user, tokens } = await register(payload);
    await setSession(tokens);
    return Response.json({ user });
  } catch (error) {
    return failure(error);
  }
}
