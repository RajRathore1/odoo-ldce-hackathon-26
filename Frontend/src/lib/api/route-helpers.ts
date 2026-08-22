import { ApiError } from "@/lib/api/envelope";

// Turn whatever went wrong into the shape the auth forms read: a message to
// show at the top, plus per-field messages to hang off the inputs.
export function failure(error: unknown) {
  if (error instanceof ApiError) {
    // A response carrying a body cannot use 1xx/204/304, and an upstream
    // timeout should not masquerade as a client error.
    const status = error.status >= 400 ? error.status : 502;
    return Response.json(
      { message: error.message, fields: error.fields },
      { status },
    );
  }

  console.error("Backend request failed", error);
  return Response.json(
    { message: "Could not reach the server. Try again in a moment." },
    { status: 502 },
  );
}
