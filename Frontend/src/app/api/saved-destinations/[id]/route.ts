import { failure } from "@/lib/api/route-helpers";
import { apiFetchWithRefresh } from "@/lib/api/session";

export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;

  try {
    await apiFetchWithRefresh(`/users/me/saved-destinations/${id}/`, {
      method: "DELETE",
    });
    return Response.json({ ok: true });
  } catch (error) {
    return failure(error);
  }
}
