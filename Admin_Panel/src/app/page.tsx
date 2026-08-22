import { AdminShell } from "@/components/admin-shell";
import { AnalyticsPanel } from "@/components/analytics-panel";
import {
  ActivityIcon,
  ChartIcon,
  MapPinIcon,
  UsersIcon,
  WalletIcon,
} from "@/components/icons";
import { PanelCard } from "@/components/panel-card";
import { RankingList } from "@/components/ranking-list";
import { StatCard } from "@/components/stat-card";
import { UsersTable } from "@/components/users-table";
import {
  platformStats,
  popularActivities,
  popularCities,
  users,
} from "@/lib/mock-data";

const money = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
  notation: "compact",
});

const fullMoney = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

export default function AdminDashboardPage() {
  return (
    <AdminShell>
      <div className="space-y-8">
        <header id="overview">
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
            trend="+6.4%"
            icon={UsersIcon}
            tone="primary"
          />
          <StatCard
            label="Trips planned"
            value={platformStats.tripsPlanned.toLocaleString("en-IN")}
            trend="+11.2%"
            icon={MapPinIcon}
            tone="accent"
          />
          <StatCard
            label="Total revenue"
            value={money.format(platformStats.totalRevenue)}
            trend="+8.9%"
            icon={WalletIcon}
            tone="success"
          />
          <StatCard
            label="Avg. trip budget"
            value={fullMoney.format(platformStats.avgBudget)}
            icon={ChartIcon}
            tone="info"
          />
          <StatCard
            label="Active users"
            value={platformStats.activeUsers.toLocaleString("en-IN")}
            icon={UsersIcon}
            tone="success"
          />
          <StatCard
            label="Cities covered"
            value={platformStats.citiesCovered.toLocaleString("en-IN")}
            icon={MapPinIcon}
            tone="primary"
          />
          <StatCard
            label="New sign-ups (this month)"
            value={platformStats.newSignupsThisMonth.toLocaleString("en-IN")}
            trend="+19%"
            icon={ChartIcon}
            tone="accent"
          />
          <StatCard
            label="Community posts"
            value={platformStats.communityPosts.toLocaleString("en-IN")}
            icon={ActivityIcon}
            tone="warning"
          />
        </div>

        <div id="cities" className="grid gap-6 lg:grid-cols-2">
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

          <div id="activities">
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
        </div>

        <div id="analytics">
          <AnalyticsPanel />
        </div>

        <div id="users">
          <PanelCard
            title="Manage users"
            description="Search, filter and moderate accounts."
          >
            <UsersTable users={users} />
          </PanelCard>
        </div>
      </div>
    </AdminShell>
  );
}
