import Link from "next/link";
import { cn } from "@/lib/cn";
import { coverGradients } from "@/lib/covers";
import { formatMoney } from "@/lib/format";
import type { Region } from "@/lib/types";

export function RegionCard({ region }: { region: Region }) {
  return (
    <Link
      href={`/explore?region=${region.id}`}
      className="group block w-60 shrink-0 snap-start sm:w-64"
    >
      <div
        className={cn(
          "relative h-44 overflow-hidden rounded-2xl bg-gradient-to-br",
          coverGradients[region.cover],
        )}
      >
        <div className="absolute inset-0 bg-black/0 transition-colors duration-200 group-hover:bg-black/10" />
        <span className="absolute bottom-3 left-3 rounded-full bg-surface/90 px-2.5 py-1 text-xs font-medium text-primary shadow-sm backdrop-blur-sm">
          {region.tripCount} trips
        </span>
      </div>

      <h3 className="mt-3 text-sm font-semibold">{region.name}</h3>
      <p className="mt-0.5 line-clamp-1 text-sm text-text-muted">
        {region.blurb}
      </p>
      <p className="mt-1 text-sm">
        <span className="font-semibold">{formatMoney(region.fromPrice)}</span>
        <span className="text-text-muted"> to start</span>
      </p>
    </Link>
  );
}
