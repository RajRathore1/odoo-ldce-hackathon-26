import { PanelCard } from "@/components/panel-card";
import { RankingList } from "@/components/ranking-list";
import { SignupsChart } from "@/components/signups-chart";
import { StatCard } from "@/components/stat-card";
import { UsersTable } from "@/components/users-table";
import {
  monthlySignups,
  platformStats,
  popularActivities,
  popularCities,
  users,
} from "@/lib/mock-data";

const money = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

export default function AdminDashboardPage() {
  return (
    <div className="mx-auto w-full max-w-6xl flex-1 space-y-8 px-4 py-8 sm:px-6 sm:py-10">
      <header>
        <p className="text-sm font-medium text-accent">GlobeTrotter Admin</p>
        <h1 className="mt-1 font-heading text-3xl font-semibold sm:text-4xl">
          Platform overview
        </h1>
        <p className="mt-2 max-w-xl text-text-muted">
          Users, popular destinations and trends across the platform.
        </p>
      </header>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Total users"
          value={platformStats.totalUsers.toLocaleString("en-IN")}
        />
        <StatCard
          label="Trips planned"
          value={platformStats.tripsPlanned.toLocaleString("en-IN")}
        />
        <StatCard
          label="Cities covered"
          value={platformStats.citiesCovered.toLocaleString("en-IN")}
        />
        <StatCard
          label="Avg. trip budget"
          value={money.format(platformStats.avgBudget)}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <PanelCard
          title="Popular cities"
          description="Ranked by trips planned this year."
        >
          <RankingList
            items={popularCities.map((city) => ({
              label: city.city,
              sublabel: city.country,
              value: city.trips,
            }))}
          />
        </PanelCard>

        <PanelCard
          title="Popular activities"
          description="Ranked by bookings across all trips."
        >
          <RankingList
            items={popularActivities.map((activity) => ({
              label: activity.activity,
              value: activity.bookings,
            }))}
          />
        </PanelCard>
      </div>

      <PanelCard
        title="User trends & analytics"
        description="New sign-ups over the last 6 months."
      >
        <SignupsChart data={monthlySignups} />
      </PanelCard>

      <PanelCard
        title="Manage users"
        description="Search, review activity and moderate accounts."
      >
        <UsersTable users={users} />
      </PanelCard>
    </div>
  );
}
