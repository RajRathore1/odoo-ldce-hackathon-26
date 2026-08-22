import { redirect } from "next/navigation";
import { ProfileForm } from "@/components/profile-form";
import { SectionHeader } from "@/components/section-header";
import { TripCard } from "@/components/trip-card";
import { listCities, listCountries } from "@/lib/api/geo-service";
import { apiFetch, getCurrentUser } from "@/lib/api/session";
import { listTrips } from "@/lib/api/trips-service";

type Stats = {
  total_trips: number;
  ongoing: number;
  upcoming: number;
  completed: number;
  cities_visited: number;
  countries_visited: number;
};

export default async function ProfilePage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login");

  const [countries, cities, trips, stats] = await Promise.all([
    listCountries(),
    listCities(),
    listTrips(),
    apiFetch<Stats>("/users/me/stats/"),
  ]);

  const preplanned = trips.filter((trip) => trip.status === "upcoming");
  const previous = trips.filter((trip) => trip.status !== "upcoming");

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

      <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label="Trips" value={stats.total_trips} />
        <Stat label="Up-coming" value={stats.upcoming} />
        <Stat label="Completed" value={stats.completed} />
        <Stat label="Cities visited" value={stats.cities_visited} />
      </dl>

      <ProfileForm
        user={user}
        countries={countries.map((country) => ({
          label: country.name,
          value: String(country.id),
        }))}
        cities={cities.map((city) => ({
          label: `${city.name}, ${city.country}`,
          value: city.id,
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
