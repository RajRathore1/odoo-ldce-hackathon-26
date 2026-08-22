import type { SavedDestinationDto } from "@/lib/api/geo-service";
import { failure } from "@/lib/api/route-helpers";
import { apiFetchWithRefresh } from "@/lib/api/session";

export async function POST(request: Request) {
  const body = (await request.json()) as { city: number; note?: string };

  try {
    const saved = await apiFetchWithRefresh<SavedDestinationDto>(
      "/users/me/saved-destinations/",
      { method: "POST", body: JSON.stringify(body) },
    );
    return Response.json({ saved });
  } catch (error) {
    return failure(error);
  }
}
