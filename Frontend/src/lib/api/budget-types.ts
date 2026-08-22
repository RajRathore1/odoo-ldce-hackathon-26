import type { Paginated } from "@/lib/api/trips-service";

export type { Paginated };

export const expenseCategories = [
  { label: "Transport", value: "TRANSPORT" },
  { label: "Stay", value: "STAY" },
  { label: "Activities", value: "ACTIVITY" },
  { label: "Meals", value: "MEALS" },
  { label: "Shopping", value: "SHOPPING" },
  { label: "Other", value: "OTHER" },
];

export type BudgetDto = {
  currency: string;
  total_budget: string | null;
  grand_total: string;
  remaining: string | null;
  is_over_budget: boolean;
  avg_cost_per_day: string;
  breakdown: {
    category: string;
    label: string;
    amount: string;
    percentage: number;
  }[];
  by_stop: {
    stop_id: number;
    title: string;
    budget: string | null;
    spent: string;
    is_over_budget: boolean;
  }[];
  by_day: { date: string; amount: string; is_over_budget: boolean }[];
  alerts: { type: string; date: string; message: string }[];
};

export type ExpenseDto = {
  id: number;
  category: string;
  category_label: string;
  title: string;
  amount: string;
  currency: string;
  trip_stop: number | null;
  incurred_on: string | null;
  is_estimated: boolean;
  notes: string;
};
