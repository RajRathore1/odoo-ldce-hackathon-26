"use client";

import Image from "next/image";
import Link from "next/link";
import { use } from "react";
import { ErrorBlock, LoadingBlock } from "@/components/page-state";
import { SaveDestinationButton } from "@/components/save-destination-button";
import { SectionHeader } from "@/components/section-header";
import { Badge } from "@/components/ui/badge";
import { buttonStyles } from "@/components/ui/button";
import { cityImage } from "@/lib/api/adapters";
import type { CityDetailDto, SavedDestinationDto } from "@/lib/api/geo-service";
import type { Paginated } from "@/lib/api/trips-service";
import { useApi } from "@/lib/api/use-api";
import { formatMoney } from "@/lib/format";

export default function CityPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const city = useApi<CityDetailDto>(`/cities/${id}/`);
  const saved = useApi<Paginated<SavedDestinationDto>>(
    "/users/me/saved-destinations/?page_size=100",
  );

  if (city.loading) return <LoadingBlock label="Loading city" />;
  if (city.error) {
    return <ErrorBlock message={city.error} onRetry={city.reload} />;
  }
  if (!city.data) return null;

  const dto = city.data;
  const savedRow = (saved.data?.results ?? []).find(
    (row) => row.city.id === dto.id,
  );

  return (
    <div className="space-y-10">
      <div className="relative h-56 overflow-hidden rounded-3xl sm:h-72">
        <Image
          src={cityImage(dto.id, dto.image_url)}
          alt={dto.name}
          fill
          priority
          sizes="100vw"
          className="object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />
        <div className="absolute right-6 bottom-6 left-6 text-white">
          <p className="text-sm font-medium text-white/80">
            {[dto.state, dto.region].filter(Boolean).join(" - ")}
          </p>
          <h1 className="mt-1 font-heading text-3xl font-semibold sm:text-4xl">
            {dto.name}
          </h1>
        </div>
      </div>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-2xl">
          {dto.description && (
            <p className="text-text-muted">{dto.description}</p>
          )}
          <div className="mt-4 flex flex-wrap gap-2">
            <Badge tone="info">{dto.country.name}</Badge>
            <Badge tone="accent">{dto.activities_count} activities</Badge>
            <Badge tone="neutral">
              {formatMoney(Number(dto.avg_daily_cost) || 0, dto.currency)} a day
            </Badge>
          </div>
        </div>

        <div className="flex gap-3">
          <SaveDestinationButton cityId={dto.id} savedId={savedRow?.id ?? null} />
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

        {dto.top_activities.length > 0 ? (
          <div className="grid grid-cols-[repeat(auto-fit,minmax(260px,1fr))] gap-4">
            {dto.top_activities.map((activity) => (
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
