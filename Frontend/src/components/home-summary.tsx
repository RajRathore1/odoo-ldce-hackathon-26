import Link from "next/link";
import { buttonStyles } from "@/components/ui/button";
import type { DashboardDto } from "@/lib/api/dashboard-service";
import { formatDateRange, formatMoney } from "@/lib/format";

export function HomeSummary({ dashboard }: { dashboard: DashboardDto }) {
  const { counts, ongoing_trip: ongoing, budget_highlights: budget } =
    dashboard;

  if (counts.total_trips === 0) return null;

  const currency = budget.currency || "INR";

  return (
    <section className="space-y-4">
      {ongoing && (
        <Link
          href={`/trips/${ongoing.id}`}
          className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-warning/30 bg-warning/10 p-5 transition-shadow hover:shadow-md"
        >
          <div>
            <p className="inline-flex items-center gap-2 text-sm font-medium">
              <span className="size-1.5 rounded-full bg-warning" />
              On this trip right now
            </p>
            <h2 className="mt-1 font-heading text-xl font-semibold">
              {ongoing.name}
            </h2>
            <p className="mt-1 text-sm text-text-muted">
              {formatDateRange(ongoing.start_date, ongoing.end_date)} ·{" "}
              {ongoing.stops_count}{" "}
              {ongoing.stops_count === 1 ? "stop" : "stops"}
            </p>
          </div>
          <p className="text-sm font-semibold">
            {ongoing.days_remaining}{" "}
            {ongoing.days_remaining === 1 ? "day" : "days"} to go
          </p>
        </Link>
      )}

      <dl className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Tile label="Trips" value={String(counts.total_trips)} />
        <Tile label="Up-coming" value={String(counts.upcoming)} />
        <Tile
          label="Planned spend"
          value={formatMoney(Number(budget.total_planned) || 0, currency)}
        />
        <Tile
          label="Average per trip"
          value={formatMoney(Number(budget.avg_cost_per_trip) || 0, currency)}
        />
      </dl>

      {budget.over_budget_trips > 0 && (
        <p className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-danger/25 bg-danger/8 px-5 py-4 text-sm">
          <span>
            {budget.over_budget_trips}{" "}
            {budget.over_budget_trips === 1 ? "trip is" : "trips are"} over
            budget.
          </span>
          <Link href="/trips" className={buttonStyles("outline", "sm")}>
            Review them
          </Link>
        </p>
      )}
    </section>
  );
}

function Tile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-border bg-surface p-4">
      <dt className="text-sm text-text-muted">{label}</dt>
      <dd className="mt-1 font-heading text-xl font-semibold sm:text-2xl">
        {value}
      </dd>
    </div>
  );
}
