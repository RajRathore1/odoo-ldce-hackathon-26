import { failure } from "@/lib/api/route-helpers";
import { apiFetchWithRefresh } from "@/lib/api/session";

type StopPayload = {
  city: number;
  start_date: string;
  end_date: string;
  title?: string;
  budget?: string;
  notes?: string;
};

export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const { stops } = (await request.json()) as { stops: StopPayload[] };

  try {
    // Order is assigned server-side as max(order) + 1, so post them in turn to
    // keep the sections in the order the user arranged them.
    for (const stop of stops) {
      await apiFetchWithRefresh(`/trips/${id}/stops/`, {
        method: "POST",
        body: JSON.stringify(stop),
      });
    }
    return Response.json({ ok: true });
  } catch (error) {
    return failure(error);
  }
}
