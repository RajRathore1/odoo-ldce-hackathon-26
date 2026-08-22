import { apiFetch } from "@/lib/api/session";
import type { BudgetDto, ExpenseDto, Paginated } from "@/lib/api/budget-types";

export function getBudget(tripId: string) {
  return apiFetch<BudgetDto>(`/trips/${tripId}/budget/`);
}

export async function listExpenses(tripId: string) {
  const page = await apiFetch<Paginated<ExpenseDto>>(
    `/trips/${tripId}/expenses/?page_size=100`,
  );
  return page.results;
}
