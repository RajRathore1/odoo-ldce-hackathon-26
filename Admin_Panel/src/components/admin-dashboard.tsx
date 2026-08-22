"use client";

import { useEffect, useMemo, useState } from "react";
import {
  ActivityIcon,
  ChartIcon,
  MapPinIcon,
  UsersIcon,
  WalletIcon,
} from "@/components/icons";
// One tone per icon, always — Users=primary, MapPin=accent, Wallet=success,
// Chart=info, Activity=warning. Keeps icon color meaningful instead of ad hoc.
import { PanelCard } from "@/components/panel-card";
import { RankingList } from "@/components/ranking-list";
import { StatCard } from "@/components/stat-card";
import { TrendBarChart } from "@/components/trend-bar-chart";
import { UsersTable } from "@/components/users-table";
import { fetchAdminUsers } from "@/lib/admin-api";
import { cn } from "@/lib/cn";
import {
  activityCategory,
  dashboardByPeriod,
  periods,
  staticStats,
  users as mockUsers,
  type AdminUser,
  type Period,
} from "@/lib/mock-data";

type ActivityFilter = "all" | "culture" | "nature" | "adventure";

const activityFilters: { value: ActivityFilter; label: string }[] = [
  { value: "all", label: "All" },
  { value: "culture", label: "Culture" },
  { value: "nature", label: "Nature" },
  { value: "adventure", label: "Adventure" },
];

const moneyCompact = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 1,
  notation: "compact",
});

const moneyFull = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

const percent = new Intl.NumberFormat("en-IN", {
  minimumFractionDigits: 0,
});

export function AdminDashboard() {
  const [period, setPeriod] = useState<Period>("30d");
  const [liveBump, setLiveBump] = useState(0);
  const [secondsAgo, setSecondsAgo] = useState(0);
  const [country, setCountry] = useState("all");
  const [activityFilter, setActivityFilter] = useState<ActivityFilter>("all");
  const [liveUsers, setLiveUsers] = useState<AdminUser[] | null>(null);

  useEffect(() => {
    fetchAdminUsers()
      .then((result) => {
        setLiveUsers(
          result.results.map((user) => ({
            id: String(user.id),
            name: user.full_name || user.email,
            email: user.email,
            city: user.city_name ?? user.country_name ?? "—",
            trips: user.trips_count,
            joined: user.created_at.slice(0, 10),
            status: user.is_active ? "active" : "suspended",
          })),
        );
      })
      .catch(() => setLiveUsers(null));
  }, []);

  useEffect(() => {
    const bumpTimer = window.setInterval(() => {
      setLiveBump((current) => current + Math.floor(Math.random() * 3) + 1);
      setSecondsAgo(0);
    }, 5000);

    const clockTimer = window.setInterval(() => {
      setSecondsAgo((current) => current + 1);
    }, 1000);

    return () => {
      window.clearInterval(bumpTimer);
      window.clearInterval(clockTimer);
    };
  }, []);

  const data = dashboardByPeriod[period];
  const periodLabel =
    periods.find((option) => option.value === period)?.label ?? "";

  const countryOptions = useMemo(
    () => ["all", ...new Set(data.cities.map((city) => city.country))],
    [data.cities],
  );

  const filteredCities = useMemo(
    () =>
      country === "all"
        ? data.cities
        : data.cities.filter((city) => city.country === country),
    [data.cities, country],
  );

  const filteredActivities = useMemo(
    () =>
      activityFilter === "all"
        ? data.activities
        : data.activities.filter(
            (activity) => activityCategory[activity.activity] === activityFilter,
          ),
    [data.activities, activityFilter],
  );

  return (
    <div className="space-y-8">
      <header
        id="overview"
        className="flex flex-wrap items-start justify-between gap-4"
      >
        <div>
          <p className="text-sm font-medium text-accent">GlobeTrotter Admin</p>
          <h1 className="mt-1 font-heading text-3xl font-semibold sm:text-4xl">
            Platform overview
          </h1>
          <p className="mt-2 max-w-xl text-text-muted">
            Users, popular destinations and trends across the platform.
          </p>
        </div>

        <div className="flex flex-col items-end gap-2">
          <span className="inline-flex items-center gap-1.5 text-xs font-medium text-text-muted">
            <span className="relative flex size-2">
              <span className="absolute inline-flex size-full animate-ping rounded-full bg-success/60" />
              <span className="relative inline-flex size-2 rounded-full bg-success" />
            </span>
            Live · updated {secondsAgo}s ago
          </span>

          <div
            role="group"
            aria-label="Date range"
            className="inline-flex rounded-full border border-border bg-surface p-1 text-sm shadow-sm"
          >
            {periods.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => setPeriod(option.value)}
                className={cn(
                  "rounded-full px-3 py-1.5 font-medium transition-colors",
                  period === option.value
                    ? "bg-primary text-white"
                    : "text-text-muted hover:text-text",
                )}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
      </header>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label={`Revenue · ${periodLabel}`}
          value={data.kpis.revenue}
          format={moneyCompact.format}
          icon={WalletIcon}
          trend="+8.9%"
          featured
          style={{ animationDelay: "0ms" }}
        />
        <StatCard
          label="Total users"
          value={staticStats.totalUsers + liveBump}
          icon={UsersIcon}
          tone="primary"
          trend="+6.4%"
          style={{ animationDelay: "60ms" }}
        />
        <StatCard
          label="Active users"
          value={staticStats.activeUsers}
          icon={UsersIcon}
          tone="primary"
          trend="+3.2%"
          style={{ animationDelay: "120ms" }}
        />
        <StatCard
          label={`Trips planned · ${periodLabel}`}
          value={data.kpis.tripsPlanned}
          icon={MapPinIcon}
          tone="accent"
          trend="+11.2%"
          style={{ animationDelay: "180ms" }}
        />
        <StatCard
          label="Avg. trip budget"
          value={data.kpis.avgBudget}
          format={moneyFull.format}
          icon={WalletIcon}
          tone="success"
          trend="+2.1%"
          style={{ animationDelay: "240ms" }}
        />
        <StatCard
          label={`New sign-ups · ${periodLabel}`}
          value={data.kpis.newSignups}
          icon={ChartIcon}
          tone="info"
          trend="+19%"
          style={{ animationDelay: "300ms" }}
        />
        <StatCard
          label={`Community posts · ${periodLabel}`}
          value={data.kpis.communityPosts}
          icon={ActivityIcon}
          tone="warning"
          trend="+14%"
          style={{ animationDelay: "360ms" }}
        />
        <StatCard
          label="Conversion rate"
          value={32}
          format={(value) => `${percent.format(value)}%`}
          icon={ChartIcon}
          tone="info"
          trend="+1.8%"
          style={{ animationDelay: "420ms" }}
        />
      </div>

      <div id="cities" className="grid gap-6 lg:grid-cols-2">
        <PanelCard
          title="Popular cities"
          description={`Ranked by trips planned · ${periodLabel}`}
          action={
            <select
              value={country}
              onChange={(event) => setCountry(event.target.value)}
              aria-label="Filter cities by country"
              className="cursor-pointer rounded-full border border-border bg-bg px-3 py-1.5 text-sm font-medium text-text focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/15"
            >
              {countryOptions.map((option) => (
                <option key={option} value={option}>
                  {option === "all" ? "All countries" : option}
                </option>
              ))}
            </select>
          }
        >
          {filteredCities.length > 0 ? (
            <RankingList
              items={filteredCities.map((city) => ({
                label: city.city,
                sublabel: city.country,
                value: city.trips,
              }))}
            />
          ) : (
            <EmptyPanelState message="No cities match this filter." />
          )}
        </PanelCard>

        <div id="activities">
          <PanelCard
            title="Popular activities"
            description={`Ranked by bookings · ${periodLabel}`}
            action={
              <div className="inline-flex flex-wrap gap-1 rounded-full border border-border bg-bg p-1 text-sm">
                {activityFilters.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => setActivityFilter(option.value)}
                    className={cn(
                      "rounded-full px-2.5 py-1 font-medium transition-colors",
                      activityFilter === option.value
                        ? "bg-primary text-white"
                        : "text-text-muted hover:text-text",
                    )}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            }
          >
            {filteredActivities.length > 0 ? (
              <RankingList
                items={filteredActivities.map((activity) => ({
                  label: activity.activity,
                  value: activity.bookings,
                }))}
              />
            ) : (
              <EmptyPanelState message="No activities match this filter." />
            )}
          </PanelCard>
        </div>
      </div>

      <div id="analytics">
        <PanelCard
          title="User trends & analytics"
          description={`New sign-ups · ${periodLabel}`}
        >
          <TrendBarChart data={data.signups} />
        </PanelCard>
      </div>

      <div id="users">
        <PanelCard
          title="Manage users"
          description="Search, sort, filter and moderate accounts."
        >
          <UsersTable users={liveUsers ?? mockUsers} />
        </PanelCard>
      </div>
    </div>
  );
}

function EmptyPanelState({ message }: { message: string }) {
  return (
    <p className="rounded-xl border border-dashed border-border px-4 py-8 text-center text-sm text-text-muted">
      {message}
    </p>
  );
}
