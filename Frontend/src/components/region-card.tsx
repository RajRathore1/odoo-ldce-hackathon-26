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
      <div className="relative h-44 overflow-hidden rounded-2xl bg-bg">
        <Image
          src={region.image}
          alt={region.name}
          fill
          sizes="256px"
          className="object-cover transition-transform duration-300 group-hover:scale-105"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-black/0 to-black/10 transition-colors duration-200 group-hover:from-black/60" />
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
