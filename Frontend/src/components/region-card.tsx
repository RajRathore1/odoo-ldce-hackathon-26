import Image from "next/image";
import Link from "next/link";
import { formatMoney } from "@/lib/format";
import type { Region } from "@/lib/types";

export function RegionCard({ region }: { region: Region }) {
  return (
    <Link
      href={`/explore?region=${region.id}`}
      className="group block w-60 shrink-0 snap-start sm:w-64"
    >
      <article className="flex h-full flex-col overflow-hidden rounded-2xl border border-border bg-surface transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg">
        <div className="relative h-32 overflow-hidden bg-bg">
          <Image
            src={region.image}
            alt={region.name}
            fill
            sizes="256px"
            className="object-cover transition-transform duration-300 group-hover:scale-105"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-black/0 to-black/10 transition-colors duration-200 group-hover:from-black/50" />
          <span className="absolute top-3 left-3 rounded-full bg-surface/95 px-2.5 py-1 text-xs font-medium text-primary shadow-md backdrop-blur-sm">
            {region.country}
          </span>
        </div>

        <div className="flex flex-1 flex-col gap-1.5 p-4">
          <h3 className="text-sm font-semibold">{region.name}</h3>
          <p className="line-clamp-1 text-sm text-text-muted">
            {region.blurb}
          </p>

          <div className="mt-auto flex items-center justify-between border-t border-border pt-3 text-sm">
            <span className="text-text-muted">{region.tripCount} trips</span>
            <span className="font-semibold text-primary">
              {formatMoney(region.fromPrice)}
            </span>
          </div>
        </div>
      </article>
    </Link>
  );
}
