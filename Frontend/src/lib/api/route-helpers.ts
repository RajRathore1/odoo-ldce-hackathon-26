import { ApiError } from "@/lib/api/envelope";

// Turn whatever went wrong into the shape the auth forms read: a message to
// show at the top, plus per-field messages to hang off the inputs.
export function failure(error: unknown) {
  if (error instanceof ApiError) {
    return Response.json(
      { message: error.message, fields: error.fields },
      { status: error.status },
    );
  }

  console.error("Backend request failed", error);
  return Response.json(
    { message: "Could not reach the server. Try again in a moment." },
    { status: 502 },
  );
}
