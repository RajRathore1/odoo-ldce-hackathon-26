import { failure } from "@/lib/api/route-helpers";
import { apiFetchWithRefresh } from "@/lib/api/session";
import type { CreateTripPayload, TripDto } from "@/lib/api/trips-service";

export async function POST(request: Request) {
  const payload = (await request.json()) as CreateTripPayload;

  try {
    const trip = await apiFetchWithRefresh<TripDto>("/trips/", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    return Response.json({ trip });
  } catch (error) {
    return failure(error);
  }
}
