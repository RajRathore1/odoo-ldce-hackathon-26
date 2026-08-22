import { failure } from "@/lib/api/route-helpers";
import { apiFetchWithRefresh } from "@/lib/api/session";

export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ id: string; expenseId: string }> },
) {
  const { id, expenseId } = await params;

  try {
    await apiFetchWithRefresh(`/trips/${id}/expenses/${expenseId}/`, {
      method: "DELETE",
    });
    return Response.json({ ok: true });
  } catch (error) {
    return failure(error);
  }
}
