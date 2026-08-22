import Link from "next/link";
import { cn } from "@/lib/cn";
import { StatusBadge } from "@/components/ui/badge";
import { formatDateRange, formatMoney } from "@/lib/format";
import type { CoverTone, Trip } from "@/lib/types";

const covers: Record<CoverTone, string> = {
  sunset: "from-accent to-danger",
  ocean: "from-info to-primary",
  forest: "from-success to-info",
  dusk: "from-primary to-danger",
};

type TripCardProps = {
  trip: Trip;
  href?: string;
  className?: string;
};

export function TripCard({ trip, href, className }: TripCardProps) {
  const card = (
    <article
      className={cn(
        "group flex h-full flex-col overflow-hidden rounded-xl border border-border bg-surface transition-shadow hover:shadow-md",
        className,
      )}
    >
      <div
        className={cn(
          "relative h-28 bg-gradient-to-br sm:h-32",
          covers[trip.cover],
        )}
      >
        <span className="absolute top-3 left-3 rounded-full bg-surface/90 px-2.5 py-1 text-xs font-medium text-primary">
          {trip.city}, {trip.country}
        </span>
      </div>

      <div className="flex flex-1 flex-col gap-3 p-4">
        <div className="flex items-start justify-between gap-3">
          <h3 className="text-base leading-snug font-semibold">{trip.title}</h3>
          <StatusBadge status={trip.status} />
        </div>

        <p className="text-sm text-text-muted">
          {formatDateRange(trip.startDate, trip.endDate)}
        </p>

        <div className="mt-auto flex items-center justify-between border-t border-border pt-3 text-sm">
          <span className="text-text-muted">
            {trip.stops} {trip.stops === 1 ? "stop" : "stops"}
          </span>
          <span className="font-semibold text-primary">
            {formatMoney(trip.budget)}
          </span>
        </div>
      </div>
    </article>
  );

  if (!href) return card;

  return (
    <Link href={href} className="block focus-visible:outline-none">
      {card}
    </Link>
  );
}
