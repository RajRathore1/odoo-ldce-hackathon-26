export class SubmitError extends Error {
  readonly fields: Record<string, string>;

  constructor(message: string, fields: Record<string, string> = {}) {
    super(message);
    this.name = "SubmitError";
    this.fields = fields;
  }
}

// Talks to our own route handlers, never to the backend directly - the tokens
// live in httpOnly cookies and are never readable from here.
export async function postJson<T>(path: string, body: unknown): Promise<T> {
  let response: Response;

  try {
    response = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    throw new SubmitError("Network error. Check your connection and retry.");
  }

  const payload = (await response.json().catch(() => null)) as
    | { message?: string; fields?: Record<string, string> }
    | null;

  if (!response.ok) {
    throw new SubmitError(
      payload?.message ?? "Something went wrong. Try again.",
      payload?.fields ?? {},
    );
  }

  return payload as T;
}
