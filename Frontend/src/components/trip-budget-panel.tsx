"use client";

import { useState } from "react";
import { FormAlert } from "@/components/form-alert";
import { SectionHeader } from "@/components/section-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input, Select } from "@/components/ui/field";
import { api } from "@/lib/api/client";
import { ApiError } from "@/lib/api/envelope";
import type { BudgetDto, ExpenseDto } from "@/lib/api/budget-types";
import { expenseCategories } from "@/lib/api/budget-types";
import { cn } from "@/lib/cn";
import { formatMoney } from "@/lib/format";
import type { SelectOption } from "@/lib/types";

type TripBudgetPanelProps = {
  tripId: string;
  budget: BudgetDto;
  expenses: ExpenseDto[];
  stops: SelectOption[];
  tripStart: string;
  tripEnd: string;
  onChanged: () => void;
};

export function TripBudgetPanel({
  tripId,
  budget,
  expenses,
  stops,
  tripStart,
  tripEnd,
  onChanged,
}: TripBudgetPanelProps) {
  const currency = budget.currency;
  const [open, setOpen] = useState(false);
  const [alert, setAlert] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    category: "STAY",
    title: "",
    amount: "",
    trip_stop: "",
    incurred_on: "",
  });

  const spent = Number(budget.grand_total) || 0;
  const planned = budget.total_budget ? Number(budget.total_budget) : null;
  const usedPct =
    planned && planned > 0 ? Math.min(100, (spent / planned) * 100) : 0;

  function update(key: keyof typeof form, value: string) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function addExpense(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAlert(null);
    setSaving(true);

    try {
      await api(`/trips/${tripId}/expenses/`, {
        method: "POST",
        body: {
          category: form.category,
          title: form.title,
          amount: form.amount,
          trip_stop: form.trip_stop ? Number(form.trip_stop) : null,
          incurred_on: form.incurred_on || null,
        },
      });
      setForm({
        category: "STAY",
        title: "",
        amount: "",
        trip_stop: "",
        incurred_on: "",
      });
      setOpen(false);
      onChanged();
    } catch (error) {
      setAlert(
        error instanceof ApiError
          ? error.message
          : "Could not reach the server.",
      );
    } finally {
      setSaving(false);
    }
  }

  async function removeExpense(id: number) {
    await api(`/trips/${tripId}/expenses/${id}/`, { method: "DELETE" });
    onChanged();
  }

  return (
    <section className="space-y-6">
      <SectionHeader
        title="Budget"
        description="Everything booked and planned, totalled by the backend."
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <Figure label="Planned" value={planned} currency={currency} />
        <Figure label="Estimated spend" value={spent} currency={currency} />
        <Figure
          label={budget.is_over_budget ? "Over by" : "Remaining"}
          value={budget.remaining ? Math.abs(Number(budget.remaining)) : null}
          currency={currency}
          tone={budget.is_over_budget ? "danger" : "success"}
        />
      </div>

      {planned !== null && (
        <div className="h-2 overflow-hidden rounded-full bg-subtle">
          <div
            className={cn(
              "h-full rounded-full transition-[width]",
              budget.is_over_budget ? "bg-danger" : "bg-success",
            )}
            style={{ width: `${usedPct}%` }}
          />
        </div>
      )}

      {budget.alerts.length > 0 && (
        <ul className="space-y-2">
          {budget.alerts.map((alertRow) => (
            <li
              key={`${alertRow.type}-${alertRow.date}`}
              className="rounded-xl border border-warning/30 bg-warning/10 px-3.5 py-2.5 text-sm"
            >
              {alertRow.message}
            </li>
          ))}
        </ul>
      )}

      {budget.breakdown.length > 0 && (
        <div className="rounded-2xl border border-border bg-surface p-5">
          <h3 className="text-sm font-semibold">Where it goes</h3>
          <ul className="mt-4 space-y-3">
            {budget.breakdown.map((row) => (
              <li key={row.category}>
                <div className="flex items-center justify-between text-sm">
                  <span>{row.label}</span>
                  <span className="text-text-muted">
                    {formatMoney(Number(row.amount) || 0, currency)} ·{" "}
                    {row.percentage}%
                  </span>
                </div>
                <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-subtle">
                  <div
                    className="h-full rounded-full bg-primary"
                    style={{ width: `${row.percentage}%` }}
                  />
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {budget.by_stop.length > 0 && (
        <div className="rounded-2xl border border-border bg-surface p-5">
          <h3 className="text-sm font-semibold">By stop</h3>
          <ul className="mt-3 divide-y divide-border">
            {budget.by_stop.map((stop) => (
              <li
                key={stop.stop_id}
                className="flex items-center justify-between py-2.5 text-sm"
              >
                <span>{stop.title}</span>
                <span className="flex items-center gap-2">
                  <span className="text-text-muted">
                    {formatMoney(Number(stop.spent) || 0, currency)}
                    {stop.budget
                      ? ` of ${formatMoney(Number(stop.budget), currency)}`
                      : ""}
                  </span>
                  {stop.is_over_budget && <Badge tone="danger">Over</Badge>}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="rounded-2xl border border-border bg-surface p-5">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold">Expenses</h3>
          <Button variant="outline" size="sm" onClick={() => setOpen(!open)}>
            {open ? "Cancel" : "Add expense"}
          </Button>
        </div>

        {open && (
          <form onSubmit={addExpense} className="mt-4 space-y-4">
            <FormAlert message={alert} />
            <div className="grid gap-4 sm:grid-cols-2">
              <Input
                label="What was it"
                placeholder="Hotel, train tickets, dinner"
                value={form.title}
                onChange={(event) => update("title", event.target.value)}
                required
              />
              <Input
                label="Amount"
                type="number"
                min={0}
                step="0.01"
                value={form.amount}
                onChange={(event) => update("amount", event.target.value)}
                required
              />
              <Select
                label="Category"
                options={expenseCategories}
                value={form.category}
                onChange={(event) => update("category", event.target.value)}
              />
              <Select
                label="Stop"
                options={stops}
                placeholder="Whole trip"
                value={form.trip_stop}
                onChange={(event) => update("trip_stop", event.target.value)}
              />
              <Input
                label="Date"
                type="date"
                min={tripStart}
                max={tripEnd}
                value={form.incurred_on}
                onChange={(event) => update("incurred_on", event.target.value)}
                wrapperClassName="sm:col-span-2"
              />
            </div>
            <Button type="submit" disabled={saving}>
              {saving ? "Adding..." : "Add expense"}
            </Button>
          </form>
        )}

        {expenses.length > 0 ? (
          <ul className="mt-4 divide-y divide-border">
            {expenses.map((expense) => (
              <li
                key={expense.id}
                className="flex items-center justify-between gap-3 py-2.5 text-sm"
              >
                <span className="min-w-0">
                  <span className="font-medium">{expense.title}</span>
                  <span className="ml-2 text-text-muted">
                    {expense.category_label}
                    {expense.incurred_on ? ` · ${expense.incurred_on}` : ""}
                  </span>
                </span>
                <span className="flex shrink-0 items-center gap-3">
                  <span className="font-semibold">
                    {formatMoney(Number(expense.amount) || 0, expense.currency)}
                  </span>
                  <button
                    type="button"
                    onClick={() => removeExpense(expense.id)}
                    aria-label={`Remove ${expense.title}`}
                    className="rounded-full px-2 py-1 text-text-muted transition-colors hover:bg-danger/10 hover:text-danger"
                  >
                    Remove
                  </button>
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-4 text-sm text-text-muted">
            No expenses logged yet.
          </p>
        )}
      </div>
    </section>
  );
}

function Figure({
  label,
  value,
  currency,
  tone,
}: {
  label: string;
  value: number | null;
  currency: string;
  tone?: "danger" | "success";
}) {
  return (
    <div className="rounded-2xl border border-border bg-surface p-4">
      <p className="text-sm text-text-muted">{label}</p>
      <p
        className={cn(
          "mt-1 font-heading text-2xl font-semibold",
          tone === "danger" && "text-danger",
          tone === "success" && "text-success",
        )}
      >
        {value === null ? "Not set" : formatMoney(value, currency)}
      </p>
    </div>
  );
}
