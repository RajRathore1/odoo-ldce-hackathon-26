import { failure } from "@/lib/api/route-helpers";
import { apiFetchWithRefresh } from "@/lib/api/session";

type ActivityDto = {
  id: number;
  name: string;
  activity_type: string;
};

export async function GET(request: Request) {
  const city = new URL(request.url).searchParams.get("city");
  if (!city) return Response.json({ activities: [] });

  try {
    const activities = await apiFetchWithRefresh<ActivityDto[]>(
      `/activities/popular/?city=${encodeURIComponent(city)}&limit=12`,
    );
    return Response.json({
      activities: activities.map((activity) => ({
        id: String(activity.id),
        label: activity.name,
      })),
    });
  } catch (error) {
    return failure(error);
  }
}
