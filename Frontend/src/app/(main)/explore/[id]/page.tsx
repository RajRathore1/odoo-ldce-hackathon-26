import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import { SaveDestinationButton } from "@/components/save-destination-button";
import { SectionHeader } from "@/components/section-header";
import { Badge } from "@/components/ui/badge";
import { buttonStyles } from "@/components/ui/button";
import { ApiError } from "@/lib/api/envelope";
import { getCity, listSavedDestinations } from "@/lib/api/geo-service";
import { formatMoney } from "@/lib/format";

export default async function CityPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  let city;
  let saved;

  try {
    [city, saved] = await Promise.all([getCity(id), listSavedDestinations()]);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) notFound();
    throw error;
  }

  const savedRow = saved.find((row) => row.city.id === Number(id));

  return (
    <div className="space-y-10">
      <div className="relative h-56 overflow-hidden rounded-3xl sm:h-72">
        <Image
          src={city.image}
          alt={city.name}
          fill
          priority
          sizes="100vw"
          className="object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />
        <div className="absolute right-6 bottom-6 left-6 text-white">
          <p className="text-sm font-medium text-white/80">{city.blurb}</p>
          <h1 className="mt-1 font-heading text-3xl font-semibold sm:text-4xl">
            {city.name}
          </h1>
        </div>
      </div>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-2xl">
          {city.description && (
            <p className="text-text-muted">{city.description}</p>
          )}
          <div className="mt-4 flex flex-wrap gap-2">
            <Badge tone="info">{city.country}</Badge>
            <Badge tone="accent">{city.activityCount} activities</Badge>
            <Badge tone="neutral">
              {formatMoney(city.avgDailyCost, city.currency)} a day
            </Badge>
          </div>
        </div>

        <div className="flex gap-3">
          <SaveDestinationButton
            cityId={Number(id)}
            savedId={savedRow?.id ?? null}
          />
          <Link href="/trips/new" className={buttonStyles("accent")}>
            Plan a trip here
          </Link>
        </div>
      </div>

      <section>
        <SectionHeader
          title="Top activities"
          description="What other travellers book most in this city."
        />

        {city.topActivities.length > 0 ? (
          <div className="grid grid-cols-[repeat(auto-fit,minmax(260px,1fr))] gap-4">
            {city.topActivities.map((activity) => (
              <article
                key={activity.id}
                className="flex flex-col justify-between gap-3 rounded-2xl border border-border bg-surface p-4 shadow-sm transition-shadow hover:shadow-md"
              >
                <div>
                  <h3 className="font-semibold">{activity.name}</h3>
                  <p className="mt-1 text-sm text-text-muted capitalize">
                    {activity.activity_type.toLowerCase()}
                    {activity.duration_minutes
                      ? ` · ${Math.round(activity.duration_minutes / 60)}h`
                      : ""}
                  </p>
                </div>
                <div className="flex items-center justify-between border-t border-border pt-3 text-sm">
                  {activity.rating && (
                    <span className="text-text-muted">★ {activity.rating}</span>
                  )}
                  <span className="font-semibold text-primary">
                    {formatMoney(Number(activity.cost) || 0, activity.currency)}
                  </span>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <p className="rounded-2xl border border-dashed border-border px-6 py-10 text-center text-sm text-text-muted">
            Nothing listed for this city yet.
          </p>
        )}
      </section>
    </div>
  );
}
