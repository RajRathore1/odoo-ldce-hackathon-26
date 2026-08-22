import type { ExpenseDto } from "@/lib/api/budget-types";
import { failure } from "@/lib/api/route-helpers";
import { apiFetchWithRefresh } from "@/lib/api/session";

export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const payload = await request.json();

  try {
    const expense = await apiFetchWithRefresh<ExpenseDto>(
      `/trips/${id}/expenses/`,
      { method: "POST", body: JSON.stringify(payload) },
    );
    return Response.json({ expense });
  } catch (error) {
    return failure(error);
  }
}
