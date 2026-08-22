import { Suspense } from "react";
import { ExploreView } from "@/components/explore-view";

export default function ExplorePage() {
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

      <Suspense>
        <ExploreView />
      </Suspense>
    </div>
  );
}
