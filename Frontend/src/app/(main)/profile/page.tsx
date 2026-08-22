"use client";

import { useAuth } from "@/components/auth-provider";
import { ErrorBlock, LoadingBlock } from "@/components/page-state";
import { ProfileForm } from "@/components/profile-form";
import { SectionHeader } from "@/components/section-header";
import { TripCard } from "@/components/trip-card";
import { toTrip } from "@/lib/api/adapters";
import type { CityDto, CountryDto } from "@/lib/api/geo-service";
import type { Paginated, TripDto } from "@/lib/api/trips-service";
import { useApi } from "@/lib/api/use-api";

type Stats = {
  total_trips: number;
  upcoming: number;
  completed: number;
  cities_visited: number;
};

export default function ProfilePage() {
  const { user, refreshUser } = useAuth();
  const stats = useApi<Stats>("/users/me/stats/");
  const countries = useApi<Paginated<CountryDto>>("/countries/?page_size=100");
  const cities = useApi<Paginated<CityDto>>("/cities/?page_size=100");
  const trips = useApi<Paginated<TripDto>>("/trips/?page_size=100");

  if (!user || countries.loading || cities.loading) {
    return <LoadingBlock label="Loading your profile" />;
  }
  if (countries.error) {
    return <ErrorBlock message={countries.error} onRetry={countries.reload} />;
  }

  const rows = (trips.data?.results ?? []).map(toTrip);
  const preplanned = rows.filter((trip) => trip.status === "upcoming");
  const previous = rows.filter((trip) => trip.status !== "upcoming");

  return (
    <div className="space-y-10">
      <div>
        <h1 className="font-heading text-3xl font-semibold sm:text-4xl">
          Your profile
        </h1>
        <p className="mt-2 text-text-muted">
          Keep your details current so trip plans and confirmations reach the
          right place.
        </p>
      </div>

      {stats.data && (
        <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Stat label="Trips" value={stats.data.total_trips} />
          <Stat label="Up-coming" value={stats.data.upcoming} />
          <Stat label="Completed" value={stats.data.completed} />
          <Stat label="Cities visited" value={stats.data.cities_visited} />
        </dl>
      )}

      <ProfileForm
        user={user}
        onSaved={refreshUser}
        countries={(countries.data?.results ?? []).map((country) => ({
          label: country.name,
          value: String(country.id),
        }))}
        cities={(cities.data?.results ?? []).map((city) => ({
          label: `${city.name}, ${city.country.name}`,
          value: String(city.id),
        }))}
      />

      <section>
        <SectionHeader
          title="Preplanned trips"
          description="Trips you've already locked dates in for."
        />
        {preplanned.length > 0 ? (
          <div className="grid grid-cols-[repeat(auto-fit,minmax(260px,1fr))] gap-4">
            {preplanned.map((trip) => (
              <TripCard key={trip.id} trip={trip} href={`/trips/${trip.id}`} />
            ))}
          </div>
        ) : (
          <EmptyState message="No preplanned trips yet." />
        )}
      </section>

      <section>
        <SectionHeader
          title="Previous trips"
          description="Trips you've completed or are on right now."
        />
        {previous.length > 0 ? (
          <div className="grid grid-cols-[repeat(auto-fit,minmax(260px,1fr))] gap-4">
            {previous.map((trip) => (
              <TripCard key={trip.id} trip={trip} href={`/trips/${trip.id}`} />
            ))}
          </div>
        ) : (
          <EmptyState message="No previous trips yet." />
        )}
      </section>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-2xl border border-border bg-surface p-4">
      <dt className="text-sm text-text-muted">{label}</dt>
      <dd className="mt-1 font-heading text-2xl font-semibold">{value}</dd>
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <p className="rounded-2xl border border-dashed border-border px-6 py-10 text-center text-sm text-text-muted">
      {message}
    </p>
  );
}
