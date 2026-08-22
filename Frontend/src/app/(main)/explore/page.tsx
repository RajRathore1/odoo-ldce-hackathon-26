"use client";

import { Suspense } from "react";
import { ExploreView } from "@/components/explore-view";
import { ErrorBlock, LoadingBlock } from "@/components/page-state";
import { toRegion } from "@/lib/api/adapters";
import type { CityDto } from "@/lib/api/geo-service";
import type { Paginated } from "@/lib/api/trips-service";
import { useApi } from "@/lib/api/use-api";

export default function ExplorePage() {
  const { data, error, loading, reload } =
    useApi<Paginated<CityDto>>("/cities/?page_size=100");

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-heading text-3xl font-semibold sm:text-4xl">
          Explore places
        </h1>
        <p className="mt-2 max-w-xl text-text-muted">
          Search cities, regions and activities other GlobeTrotters are
          planning around.
        </p>
      </div>

      {loading && <LoadingBlock label="Loading destinations" />}
      {error && <ErrorBlock message={error} onRetry={reload} />}
      {data && (
        <Suspense>
          <ExploreView regions={data.results.map(toRegion)} />
        </Suspense>
      )}
    </div>
  );
}
