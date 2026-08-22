import { login } from "@/lib/api/auth-service";
import { setSession } from "@/lib/api/session";
import { failure } from "@/lib/api/route-helpers";

export async function POST(request: Request) {
  const { email, password } = (await request.json()) as {
    email?: string;
    password?: string;
  };

  try {
    const { user, tokens } = await login(email ?? "", password ?? "");
    await setSession(tokens);
    return Response.json({ user });
  } catch (error) {
    return failure(error);
  }
}
