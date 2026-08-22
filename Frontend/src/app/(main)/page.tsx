"use client";

import Image from "next/image";
import Link from "next/link";
import { HomeSummary } from "@/components/home-summary";
import { LandingExplorer } from "@/components/landing-explorer";
import { GlobeMark } from "@/components/navbar";
import { LoadingBlock } from "@/components/page-state";
import { buttonStyles } from "@/components/ui/button";
import { toRegion, toTrip } from "@/lib/api/adapters";
import type { DashboardDto } from "@/lib/api/dashboard-service";
import type { CityDto } from "@/lib/api/geo-service";
import type { Paginated, TripDto } from "@/lib/api/trips-service";
import { useApi } from "@/lib/api/use-api";

export default function HomePage() {
  // Three separate calls on purpose: /dashboard/ carries the counts and the
  // budget roll-up, but trims cities and costs off the rows the cards need.
  const dashboard = useApi<DashboardDto>("/dashboard/");
  const trips = useApi<Paginated<TripDto>>("/trips/?page_size=100");
  const cities = useApi<CityDto[]>("/cities/popular/?limit=8");

  const loading = dashboard.loading || trips.loading || cities.loading;

  return (
    <div className="space-y-12">
      <section className="relative overflow-hidden rounded-3xl bg-primary px-6 py-14 text-white sm:px-12 sm:py-20">
        <Image
          src="https://images.unsplash.com/photo-1482914988630-16b155655e15?fm=jpg&q=80&w=2400&auto=format&fit=crop"
          alt="Mountain range at golden hour"
          fill
          priority
          className="object-cover [filter:saturate(1.25)_contrast(1.08)_brightness(0.95)]"
        />
        <div
          aria-hidden
          className="absolute inset-0 bg-gradient-to-r from-primary/95 via-primary/70 to-primary/10"
        />
        <div
          aria-hidden
          className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-black/10"
        />
        <div
          aria-hidden
          className="absolute -top-24 -right-10 size-96 rounded-full bg-accent/30 blur-3xl mix-blend-screen"
        />

        <div className="relative max-w-2xl">
          <p className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-medium backdrop-blur-sm">
            <GlobeMark className="size-3.5 text-accent" />
            GlobeTrotter
          </p>

          <h1 className="mt-5 font-heading text-4xl leading-[1.1] font-semibold sm:text-6xl">
            Somewhere new is closer than you think.
          </h1>

          <p className="mt-5 max-w-lg text-white/70">
            Sketch the route, block out the dates, and watch the budget add up
            as you go, all before you book a thing.
          </p>

          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/trips/new" className={buttonStyles("accent", "lg")}>
              Plan a trip
            </Link>
            <Link
              href="/trips"
              className={buttonStyles(
                "outline",
                "lg",
                "border-white/25 bg-transparent text-white hover:border-white/40 hover:bg-white/10",
              )}
            >
              My trips
            </Link>
          </div>
        </div>
      </section>

      {loading ? (
        <LoadingBlock label="Loading your dashboard" />
      ) : (
        <>
          {dashboard.data && <HomeSummary dashboard={dashboard.data} />}
          <LandingExplorer
            trips={(trips.data?.results ?? []).map(toTrip)}
            regions={(cities.data ?? []).map(toRegion)}
          />
        </>
      )}
    </div>
  );
}
